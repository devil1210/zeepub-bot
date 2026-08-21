#!/usr/bin/env python3
"""
Facebook Posts Links Replacement Engine (Fase 3: Live Execution)
Ejecuta la actualización en vivo de los enlaces en Facebook Graph API v21.0
con rate limiting inteligente (1.8s entre peticiones), manejo de errores y logging.
"""

import asyncio
from datetime import datetime
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fb_replace_live")

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
            # Soporte especial para Re:Zero / Re:Vida
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
        
        # 1. Filtro estricto de Volumen
        if vol_in_post is not None and b_vol is not None:
            try:
                if float(b_vol) != float(vol_in_post):
                    continue
            except ValueError:
                continue
                
        # 2. Coincidencia de Título
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
        
        # 3. Bonus / Penalización de Color Mode
        if url_color_mode:
            if b_color == url_color_mode:
                score += 30
            elif url_color_mode == "color" and "color" in b_filename:
                score += 35
            elif url_color_mode == "bw" and ("normal" in b_filename or "[b&n]" in b_filename):
                score += 35
            else:
                score -= 40
                
        # 4. Bonus de Maquetador
        for l_name in layout_names:
            if l_name.lower() in b_layout or l_name.lower() in b_filename:
                score += 15
                break
                
        # 5. Bonus de Fansub / Traductor
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


async def execute_live_replacement():
    from core.db_manager_pg import pg_manager
    from models.communications import PublicationChannel
    from models.library import LocalBook

    await pg_manager.initialize()
    
    logger.info("📚 Cargando libros desde la base de datos...")
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
        
    logger.info(f"✅ Total libros cargados con short_link: {len(all_books)}")
    
    # Obtener todas las publicaciones
    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {
        "access_token": token,
        "fields": "id,message,created_time,permalink_url",
        "limit": "100",
    }
    
    all_posts = []
    logger.info("🌐 Descargando publicaciones de Facebook...")
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
            
    logger.info(f"📄 Publicaciones encontradas en el feed: {len(all_posts)}")
    
    # Preparar cola de posts a actualizar
    update_queue = []
    for p in all_posts:
        msg = p.get("message") or ""
        urls = URL_REGEX.findall(msg)
        download_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        
        if not download_urls:
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
                
        # Solo actualizar si todos los links fueron resueltos
        if all(r.get("new_url") is not None for r in post_replacements):
            # Calcular mensaje nuevo
            new_msg = msg
            for rep in post_replacements:
                new_msg = new_msg.replace(rep["old_url"], rep["new_url"])
                
            if new_msg != msg:
                update_queue.append({
                    "post_id": p.get("id"),
                    "created_time": p.get("created_time"),
                    "permalink_url": p.get("permalink_url"),
                    "new_message": new_msg,
                    "replacements_count": len(post_replacements),
                })
                
    total_to_update = len(update_queue)
    logger.info(f"🚀 [INICIO DE EJECUCIÓN EN VIVO] Posts a actualizar: {total_to_update}")
    
    success_count = 0
    error_count = 0
    execution_log = []
    
    async with httpx.AsyncClient(timeout=25.0) as client:
        for idx, item in enumerate(update_queue, 1):
            post_id = item["post_id"]
            new_message = item["new_message"]
            permalink = item["permalink_url"]
            
            try:
                res = await client.post(
                    f"https://graph.facebook.com/v21.0/{post_id}",
                    params={"access_token": token},
                    data={"message": new_message},
                )
                
                if res.status_code == 200 and res.json().get("success"):
                    success_count += 1
                    logger.info(f"[{idx}/{total_to_update}] ✅ Actualizado con éxito: {post_id}")
                    execution_log.append({
                        "post_id": post_id,
                        "status": "SUCCESS",
                        "permalink": permalink,
                    })
                else:
                    error_count += 1
                    logger.error(f"[{idx}/{total_to_update}] ❌ Error en post {post_id}: HTTP {res.status_code} - {res.text}")
                    execution_log.append({
                        "post_id": post_id,
                        "status": "FAILED",
                        "error": res.text,
                        "permalink": permalink,
                    })
            except Exception as e:
                error_count += 1
                logger.error(f"[{idx}/{total_to_update}] ❌ Excepción en post {post_id}: {e}")
                execution_log.append({
                    "post_id": post_id,
                    "status": "EXCEPTION",
                    "error": str(e),
                    "permalink": permalink,
                })
                
            # Pausa preventiva para proteger la cuenta contra Rate Limits de Meta
            await asyncio.sleep(1.8)
            
    # Guardar reporte de ejecución final
    final_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_attempted": total_to_update,
        "success_count": success_count,
        "error_count": error_count,
        "details": execution_log,
    }
    
    output_file = Path("data/facebook_live_replacement_execution_report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Reporte de ejecución guardado en: {output_file.resolve()}")
    
    print("\n" + "=" * 70)
    print("🎉 ACTUALIZACIÓN MASIVA EN VIVO COMPLETADA")
    print("=" * 70)
    print(f"Total publicaciones procesadas:  {total_to_update}")
    print(f"✅ Publicaciones actualizadas:   {success_count}")
    print(f"❌ Errores encontrados:          {error_count}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(execute_live_replacement())
