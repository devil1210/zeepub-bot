#!/usr/bin/env python3
"""
Facebook Posts Links Replacement Engine (Fase 4: Batch & Backoff Resilience)
Procesa de forma segura los enlaces de Facebook en lotes pequeños con pausas orgánicas
(7.5s entre posts y pausas entre bloques) para evitar el rate limit de spam de Meta.
"""

import asyncio
import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fb_replace_batch")

DOWNLOAD_DOMAINS = ["1drv.ms", "onedrive.live.com", "drive.google.com", "mediafire.com", "mega.nz"]
URL_REGEX = re.compile(
    r"https?://(?:[a-zA-Z0-9\-_]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s<>'\"`(){}[\]]*)?",
    re.IGNORECASE,
)


def extract_volume_number(text: str) -> float | None:
    patterns = [
        r"(?:volumen|vol|volume|v|tomo)\s*[\.\-:]?\s*(\d+(?:\.\d+)?)",
        r"[-─—]\s*(\d+(?:\.\d+)?)\s*$",
        r"#\s*(\d+(?:\.\d+)?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


def clean_title_candidates(text: str) -> list[str]:
    first_line = text.strip().split("\n")[0]
    first_line = re.sub(r"^epub\s+de:\s*", "", first_line, flags=re.IGNORECASE)
    parts = re.split(r"[║|]", first_line)
    
    candidates = []
    for part in parts:
        cleaned = re.sub(r"[-─—]?\s*(?:volumen|vol|volume|v|tomo)\s*[\.\-:]?\s*\d+(?:\.\d+)?.*$", "", part, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+epubs?.*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\[.*?\]", "", cleaned)
        cleaned = cleaned.strip(" -─—:.,")
        if len(cleaned) >= 3:
            candidates.append(cleaned)
            if "re:vida" in cleaned.lower() or "re:zero" in cleaned.lower():
                candidates.append("re•iniciar mi vida en otro mundo desde cero")
                candidates.append("re:iniciar mi vida en otro mundo desde cero")
            
    return candidates if candidates else [first_line.strip()]


def extract_layout_and_fansubs(text: str) -> tuple[list[str], list[str]]:
    hashtags = re.findall(r"#([a-zA-Z0-9_]+)", text)
    layout_names = [
        h for h in hashtags
        if h.lower() not in ("zeepub", "zeepubs", "novela", "novelas", "epub", "anime", "nl", "novelaligera")
    ]
    brackets = re.findall(r"\[(.*?)\]", text)
    fansubs = [b for b in brackets if not b.lower().startswith("epub")]
    return layout_names, fansubs


def detect_color_mode_context(message: str, url: str) -> str | None:
    idx = message.find(url)
    if idx != -1:
        start_idx = max(0, idx - 120)
        prefix_context = message[start_idx:idx].lower()
        if "color" in prefix_context:
            return "color"
        if "b&n" in prefix_context or "blanco y negro" in prefix_context or "b/n" in prefix_context:
            return "bw"
    return None


def match_single_link(
    message: str,
    target_url: str,
    all_books: list[dict[str, Any]],
) -> dict[str, Any] | None:
    vol_in_post = extract_volume_number(message)
    title_candidates = clean_title_candidates(message)
    layout_names, fansubs = extract_layout_and_fansubs(message)
    url_color_mode = detect_color_mode_context(message, target_url)
    
    candidates_books = []
    
    for b in all_books:
        b_title = (b.get("title") or "").lower()
        b_series_es = (b.get("series_spanish") or "").lower()
        b_series_en = (b.get("series_english") or "").lower()
        b_vol = b.get("volume")
        b_color = (b.get("color_mode") or "").lower()
        b_layout = (b.get("layout_by") or "").lower()
        b_filename = (b.get("filename") or "").lower()
        
        if vol_in_post is not None and b_vol is not None:
            try:
                if float(b_vol) != float(vol_in_post):
                    continue
            except ValueError:
                continue
                
        title_score = 0
        for cand in title_candidates:
            c = cand.lower()
            if len(c) < 4:
                continue
            if c == b_title or c == b_series_es or c == b_series_en:
                title_score = max(title_score, 100)
            elif c in b_title or b_title in c:
                title_score = max(title_score, 85)
            elif c in b_series_es or b_series_es in c:
                title_score = max(title_score, 80)
            elif c in b_series_en or b_series_en in c:
                title_score = max(title_score, 75)
                
        if title_score < 75:
            continue
            
        score = title_score
        
        if url_color_mode:
            if b_color == url_color_mode:
                score += 30
            elif url_color_mode == "color" and "color" in b_filename:
                score += 35
            elif url_color_mode == "bw" and ("normal" in b_filename or "[b&n]" in b_filename):
                score += 35
            else:
                score -= 40
                
        for l_name in layout_names:
            if l_name.lower() in b_layout or l_name.lower() in b_filename:
                score += 15
                break
                
        for f_name in fansubs:
            if f_name.lower() in b_filename:
                score += 15
                break
                
        candidates_books.append((score, b))
        
    if not candidates_books:
        return None
        
    candidates_books.sort(key=lambda x: x[0], reverse=True)
    best_score, best_book = candidates_books[0]
    
    if best_score >= 80:
        return best_book
    return None


async def run_batch_replacement(batch_size: int = 35, sleep_between_posts: float = 7.5, block_rest_minutes: int = 15):
    from core.db_manager_pg import pg_manager
    from models.communications import PublicationChannel
    from models.library import LocalBook

    await pg_manager.initialize()
    
    async with pg_manager.get_session() as session:
        res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res_chan.scalar_one_or_none()
        if not chan:
            logger.error("❌ Canal 6 no encontrado")
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
        
    logger.info(f"✅ Libros cargados en memoria: {len(all_books)}")
    
    # Obtener el feed actual de Facebook
    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {
        "access_token": token,
        "fields": "id,message,created_time,permalink_url",
        "limit": "100",
    }
    
    all_posts = []
    logger.info("🌐 Obteniendo publicaciones completas de Facebook...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            resp = await client.get(url, params=params if len(all_posts) == 0 else None)
            if resp.status_code != 200:
                break
            data = resp.json()
            posts = data.get("data", [])
            all_posts.extend(posts)
            url = data.get("paging", {}).get("next")
            params = None
            
    # Filtrar publicaciones que AÚN contienen enlaces antiguos de descarga
    pending_queue = []
    already_updated_count = 0
    
    for p in all_posts:
        msg = p.get("message") or ""
        urls = URL_REGEX.findall(msg)
        download_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        
        if not download_urls:
            if "dl.zeepubs.com" in msg:
                already_updated_count += 1
            continue
            
        post_replacements = []
        for dl_url in download_urls:
            matched_book = match_single_link(msg, dl_url, all_books)
            if matched_book:
                post_replacements.append({
                    "old_url": dl_url,
                    "new_url": f"https://dl.zeepubs.com/{matched_book['short_link']}",
                    "book_title": matched_book["title"],
                })
            else:
                post_replacements.append({
                    "old_url": dl_url,
                    "new_url": None,
                })
                
        if all(r.get("new_url") is not None for r in post_replacements):
            new_msg = msg
            for rep in post_replacements:
                new_msg = new_msg.replace(rep["old_url"], rep["new_url"])
                
            if new_msg != msg:
                pending_queue.append({
                    "post_id": p.get("id"),
                    "created_time": p.get("created_time"),
                    "permalink_url": p.get("permalink_url"),
                    "new_message": new_msg,
                })
                
    total_pending = len(pending_queue)
    logger.info(f"📊 Estado general: {already_updated_count} ya actualizados con éxito | {total_pending} pendientes por actualizar")
    
    if total_pending == 0:
        logger.info("🎉 ¡Todas las publicaciones ya han sido actualizadas!")
        return

    # Ejecutar en bucle de lotes seguros
    batch_num = 1
    total_batches = (total_pending + batch_size - 1) // batch_size
    
    async with httpx.AsyncClient(timeout=25.0) as client:
        for i in range(0, total_pending, batch_size):
            batch = pending_queue[i : i + batch_size]
            logger.info(f"🚀 Iniciando Lote {batch_num}/{total_batches} ({len(batch)} publicaciones)...")
            
            for p_idx, item in enumerate(batch, 1):
                post_id = item["post_id"]
                new_msg = item["new_message"]
                
                try:
                    res = await client.post(
                        f"https://graph.facebook.com/v21.0/{post_id}",
                        params={"access_token": token},
                        data={"message": new_msg},
                    )
                    
                    if res.status_code == 200 and res.json().get("success"):
                        logger.info(f"[{p_idx}/{len(batch)} en Lote {batch_num}] ✅ Actualizado: {post_id}")
                    elif res.status_code == 400 and "OAuthException" in res.text:
                        logger.warning(f"⚠️ Meta rate limit detectado en post {post_id}. Entrando en descanso forzado de 20 minutos...")
                        await asyncio.sleep(1200)
                        # Reintentar este mismo post
                        retry_res = await client.post(
                            f"https://graph.facebook.com/v21.0/{post_id}",
                            params={"access_token": token},
                            data={"message": new_msg},
                        )
                        if retry_res.status_code == 200:
                            logger.info(f"[{p_idx}/{len(batch)}] ✅ Actualizado tras reintento: {post_id}")
                    else:
                        logger.error(f"❌ Error en post {post_id}: HTTP {res.status_code} - {res.text}")
                except Exception as e:
                    logger.error(f"❌ Excepción en post {post_id}: {e}")
                    
                # Pausa con jitter aleatorio para imitar comportamiento humano
                jitter = random.uniform(sleep_between_posts - 1.0, sleep_between_posts + 2.0)
                await asyncio.sleep(jitter)
                
            batch_num += 1
            if i + batch_size < total_pending:
                logger.info(f"☕ Lote completado. Descanso programado de {block_rest_minutes} minutos entre lotes...")
                await asyncio.sleep(block_rest_minutes * 60)
                
    logger.info("🎉 ¡PROCESAMIENTO POR LOTES FINALIZADO CON ÉXITO!")


if __name__ == "__main__":
    asyncio.run(run_batch_replacement())
