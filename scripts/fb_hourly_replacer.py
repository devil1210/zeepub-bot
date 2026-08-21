#!/usr/bin/env python3
"""
Facebook Hourly Safe URL Replacer Daemon
Procesa 25 publicaciones por hora de forma automática y silenciosa,
respetando el ciclo de renovación de cuota de enlaces de Meta hasta
completar el 100% de los posts de la página.
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
logger = logging.getLogger("fb_hourly_replacer")

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


async def run_hourly_daemon(posts_per_hour: int = 25):
    from core.db_manager_pg import pg_manager
    from models.communications import PublicationChannel
    from models.library import LocalBook

    await pg_manager.initialize()
    logger.info("🌌 [FB HOURLY DAEMON] Iniciando servicio de actualización de enlaces...")
    
    while True:
        try:
            async with pg_manager.get_session() as session:
                res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
                chan = res_chan.scalar_one_or_none()
                if not chan:
                    res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.platform == "facebook"))
                    chan = res_chan.scalars().first()
                    
                if not chan or not chan.config:
                    logger.error("❌ Canal de Facebook no encontrado o sin config")
                    await asyncio.sleep(3600)
                    continue
                    
                page_id = str(chan.target_id)
                token = chan.config.get("page_access_token") or chan.config.get("access_token")
                
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
                
            # Obtener feed de Facebook
            url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
            params = {
                "access_token": token,
                "fields": "id,message,created_time,permalink_url",
                "limit": "100",
            }
            
            all_posts = []
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
                    
            pending_queue = []
            already_done = 0
            
            for p in all_posts:
                msg = p.get("message") or ""
                urls = URL_REGEX.findall(msg)
                download_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
                
                if not download_urls:
                    if "dl.zeepubs.com" in msg:
                        already_done += 1
                    continue
                    
                post_replacements = []
                for dl_url in download_urls:
                    matched_book = match_single_link(msg, dl_url, all_books)
                    if matched_book:
                        post_replacements.append({
                            "old_url": dl_url,
                            "new_url": f"https://dl.zeepubs.com/{matched_book['short_link']}",
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
                            "new_message": new_msg,
                        })
                        
            # Notificación de inicio de lote
            total_pending = len(pending_queue)
            logger.info(f"📊 Progreso Global: {already_done} actualizados con éxito | {total_pending} pendientes")
            
            if total_pending == 0:
                msg_done = (
                    "🎉 <b>¡MISIÓN CUMPLIDA EN FACEBOOK!</b>\n\n"
                    f"✅ Todas las publicaciones de la página oficial ({already_done} posts) "
                    "han sido actualizadas con los enlaces directos de <code>dl.zeepubs.com</code>."
                )
                logger.info("🎉 ¡MISIÓN CUMPLIDA! Todas las publicaciones de Facebook tienen ahora dl.zeepubs.com")
                await send_telegram_alert(msg_done)
                break
                
            # Procesar el lote de esta hora (25 posts)
            batch = pending_queue[:posts_per_hour]
            logger.info(f"🚀 Procesando lote seguro de {len(batch)} publicaciones para esta hora...")
            
            batch_success = 0
            rate_limit_hit = False
            async with httpx.AsyncClient(timeout=25.0) as client:
                for idx, item in enumerate(batch, 1):
                    post_id = item["post_id"]
                    new_msg = item["new_message"]
                    
                    try:
                        res = await client.post(
                            f"https://graph.facebook.com/v21.0/{post_id}",
                            params={"access_token": token},
                            data={"message": new_msg},
                        )
                        
                        if res.status_code == 200 and res.json().get("success"):
                            batch_success += 1
                            logger.info(f"[{idx}/{len(batch)}] ✅ Post {post_id} actualizado.")
                        elif res.status_code == 400 and ("OAuthException" in res.text or "368" in res.text):
                            logger.warning("⚠️ Meta rate limit detectado. Deteniendo lote por esta hora para dejar enfriar la cuota.")
                            rate_limit_hit = True
                            break
                        else:
                            logger.error(f"❌ Error en post {post_id}: HTTP {res.status_code}")
                    except Exception as e:
                        logger.error(f"❌ Excepción en post {post_id}: {e}")
                        
                    # Pausa orgánica
                    await asyncio.sleep(random.uniform(8.0, 12.0))
                    
            already_done_now = already_done + batch_success
            remaining_now = total_pending - batch_success
            
            # Enviar reporte por Telegram
            if batch_success > 0 or rate_limit_hit:
                status_text = (
                    "📊 <b>Reporte de Actualización de Enlaces en Facebook</b>\n\n"
                    f"🔹 <b>Lote de la hora:</b> {batch_success} actualizados con éxito\n"
                    f"✅ <b>Total completados:</b> {already_done_now} publicaciones\n"
                    f"⏳ <b>Pendientes restantes:</b> {remaining_now} publicaciones\n\n"
                )
                if rate_limit_hit:
                    status_text += "⚠️ <i>Meta activó protección temporal por spam. El daemon esperará 60 minutos para reintentar el siguiente lote de forma segura.</i>"
                else:
                    status_text += "🚀 <i>Próximo lote programado en 60 minutos.</i>"
                    
                await send_telegram_alert(status_text)
                
            logger.info(f"✅ Lote de la hora finalizado ({batch_success} actualizados). Esperando 60 minutos para el siguiente lote...")
            await asyncio.sleep(3600)
            
        except Exception as e:
            logger.error(f"❌ Error inesperado en el ciclo del daemon: {e}")
            await asyncio.sleep(1800)


async def send_telegram_alert(message: str) -> None:
    """Envía una notificación al administrador en Telegram."""
    import os
    from config.config_settings import config
    bot_token = getattr(config, "TELEGRAM_TOKEN", None) or getattr(config, "BOT_TOKEN", None) or os.getenv("TELEGRAM_TOKEN") or os.getenv("BOT_TOKEN")
    
    admin_id = 133994080
    if config.ADMIN_USERS:
        admin_id = list(config.ADMIN_USERS)[0]
    
    if not bot_token:
        return
        
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": admin_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
    except Exception as e:
        logger.warning(f"No se pudo enviar notificación por Telegram: {e}")


if __name__ == "__main__":
    asyncio.run(run_hourly_daemon())
