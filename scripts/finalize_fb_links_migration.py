#!/usr/bin/env python3
"""
Finalize Facebook Links Migration
Actualiza las publicaciones pendientes con enlaces antiguos (OneDrive, Google Drive, etc.)
por los enlaces oficiales directos de dl.zeepubs.com, respetando pausas orgánicas y políticas de Meta.
"""

import asyncio
import json
import logging
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from models.library import LocalBook
from scripts.execute_fb_replace_batch import (
    DOWNLOAD_DOMAINS,
    URL_REGEX,
    match_single_link,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("finalize_fb_migration")


async def run_final_migration():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res_chan = await session.execute(
            select(PublicationChannel).where(PublicationChannel.id == 6)
        )
        chan = res_chan.scalar_one_or_none()
        if not chan:
            logger.error("❌ No se encontró el canal de Facebook (ID 6).")
            return

        page_id = str(chan.target_id)
        token = chan.config.get("page_access_token")

        res_books = await session.execute(select(LocalBook))
        raw_books = res_books.scalars().all()
        all_books = [
            {
                "id": str(b.id),
                "title": b.title,
                "volume": b.volume,
                "short_link": b.short_link,
                "series_spanish": b.series_spanish,
                "series_english": b.series_english,
                "color_mode": b.color_mode,
                "layout_by": b.layout_by,
                "translator": b.translator,
                "filename": b.filename,
            }
            for b in raw_books
            if b.short_link
        ]

    logger.info(f"📚 {len(all_books)} libros cargados desde la base de datos.")

    # 1. Obtener todas las publicaciones del feed de Facebook
    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {
        "access_token": token,
        "fields": "id,message,created_time,permalink_url",
        "limit": "100",
    }
    all_posts = []

    logger.info("🔍 Consultando feed completo de la página de Facebook...")
    async with httpx.AsyncClient(timeout=35.0) as client:
        while url:
            resp = await client.get(url, params=params if len(all_posts) == 0 else None)
            if resp.status_code != 200:
                logger.error(f"❌ Error al paginar publicaciones: {resp.status_code} - {resp.text}")
                break
            data = resp.json()
            posts = data.get("data", [])
            all_posts.extend(posts)
            url = data.get("paging", {}).get("next")
            params = None

    logger.info(f"📰 Total publicaciones recuperadas: {len(all_posts)}")

    # 2. Filtrar y preparar reemplazos
    pending_tasks = []
    already_migrated = 0

    for p in all_posts:
        msg = p.get("message") or ""
        urls = URL_REGEX.findall(msg)
        dl_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]

        if not dl_urls:
            if "dl.zeepubs.com" in msg:
                already_migrated += 1
            continue

        replacements = []
        for dl in dl_urls:
            matched = match_single_link(msg, dl, all_books)
            if matched:
                replacements.append({
                    "old_url": dl,
                    "new_url": f"https://dl.zeepubs.com/{matched['short_link']}",
                    "title": matched["title"],
                })
            else:
                replacements.append({
                    "old_url": dl,
                    "new_url": None,
                    "title": None,
                })

        new_msg = msg
        can_replace_all = all(r["new_url"] is not None for r in replacements)

        if can_replace_all:
            for rep in replacements:
                new_msg = new_msg.replace(rep["old_url"], rep["new_url"])

            if new_msg != msg:
                pending_tasks.append({
                    "post_id": p.get("id"),
                    "created_time": p.get("created_time"),
                    "permalink_url": p.get("permalink_url"),
                    "new_message": new_msg,
                    "replacements": replacements,
                })

    total = len(pending_tasks)
    logger.info(f"📊 Estado: {already_migrated} ya actualizados | {total} pendientes para migrar.")

    if total == 0:
        logger.info("🎉 ¡No hay publicaciones pendientes! Todas están al día.")
        return

    # 3. Ejecutar reemplazo controlado
    success_count = 0
    fallback_comment_count = 0
    failed_count = 0

    log_path = Path("/app/fb_finalize_migration.log")
    with open(log_path, "w", encoding="utf-8") as log_f:
        log_f.write(f"[{datetime.now().isoformat()}] Iniciando migración final de {total} publicaciones...\n")

        async with httpx.AsyncClient(timeout=30.0) as client:
            for idx, item in enumerate(pending_tasks, 1):
                post_id = item["post_id"]
                new_msg = item["new_message"]
                reps = item["replacements"]
                books_desc = ", ".join([r["title"] or "Desconocido" for r in reps])

                logger.info(f"[{idx}/{total}] Procesando post {post_id} ({books_desc})...")

                try:
                    # Intento directo de edición del post
                    res = await client.post(
                        f"https://graph.facebook.com/v21.0/{post_id}",
                        params={"access_token": token},
                        data={"message": new_msg},
                    )

                    if res.status_code == 200 and res.json().get("success"):
                        success_count += 1
                        log_msg = f"[{idx}/{total}] ✅ Post {post_id} actualizado exitosamente vía edición directa.\n"
                        logger.info(log_msg.strip())
                        log_f.write(log_msg)
                    elif res.status_code == 400 and ("368" in res.text or "Rate limit" in res.text):
                        logger.warning(f"⚠️ Meta rate limit detectado en post {post_id}. Pausando 120 segundos...")
                        log_f.write(f"[{idx}/{total}] ⚠️ Rate limit temporal en {post_id}. Pausando 120s.\n")
                        await asyncio.sleep(120)
                        # Reintento tras pausa
                        res_retry = await client.post(
                            f"https://graph.facebook.com/v21.0/{post_id}",
                            params={"access_token": token},
                            data={"message": new_msg},
                        )
                        if res_retry.status_code == 200 and res_retry.json().get("success"):
                            success_count += 1
                            log_msg = f"[{idx}/{total}] ✅ Post {post_id} actualizado tras pausa.\n"
                            logger.info(log_msg.strip())
                            log_f.write(log_msg)
                        else:
                            failed_count += 1
                            log_f.write(f"[{idx}/{total}] ❌ Falló tras reintento en {post_id}: {res_retry.text}\n")
                    else:
                        # Fallback: Si no permite edición de mensaje (ej. objeto antiguo), publicar comentario oficial
                        logger.warning(f"⚠️ No se pudo editar directamente ({res.status_code}). Aplicando fallback de comentario...")
                        comment_links = "\n".join([f"• {r['title']}: {r['new_url']}" for r in reps])
                        comment_msg = f"📌 Enlace(s) de descarga oficial(es) actualizado(s) [EPUB3]:\n{comment_links}"

                        c_res = await client.post(
                            f"https://graph.facebook.com/v21.0/{post_id}/comments",
                            params={"access_token": token},
                            data={"message": comment_msg},
                        )
                        if c_res.status_code == 200:
                            fallback_comment_count += 1
                            log_msg = f"[{idx}/{total}] 💬 Comentario oficial publicado en post {post_id}.\n"
                            logger.info(log_msg.strip())
                            log_f.write(log_msg)
                        else:
                            failed_count += 1
                            log_msg = f"[{idx}/{total}] ❌ Falló edición y comentario en post {post_id}: {c_res.status_code} - {c_res.text}\n"
                            logger.error(log_msg.strip())
                            log_f.write(log_msg)

                except Exception as e:
                    failed_count += 1
                    err_msg = f"[{idx}/{total}] ❌ Excepción en post {post_id}: {e}\n"
                    logger.error(err_msg.strip())
                    log_f.write(err_msg)

                # Pausa orgánica con jitter entre 8 y 12 segundos
                pause = random.uniform(8.0, 12.0)
                await asyncio.sleep(pause)

        summary = (
            f"\n==================================================\n"
            f"🎉 MIGRACIÓN FINALIZADA:\n"
            f"   ✅ Editados directamente: {success_count}\n"
            f"   💬 Fallback comentados:   {fallback_comment_count}\n"
            f"   ❌ Fallidos:              {failed_count}\n"
            f"   📊 Total procesados:      {total}\n"
            f"==================================================\n"
        )
        logger.info(summary)
        log_f.write(summary)


if __name__ == "__main__":
    asyncio.run(run_final_migration())
