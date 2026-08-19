#!/usr/bin/env python3
"""
Facebook Posts Links Replacement Engine (Fase 3: Dry-Run & Live)
Mapea TODAS las 601 publicaciones de Facebook contra los 856 libros en BD
para reemplazar enlaces de descarga (1drv.ms, onedrive, mega, mediafire, drive)
por los enlaces oficiales https://dl.zeepubs.com/{short_link}.
"""

import asyncio
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fb_replace")

DOWNLOAD_DOMAINS = ["1drv.ms", "onedrive.live.com", "drive.google.com", "mediafire.com", "mega.nz"]
URL_REGEX = re.compile(
    r"https?://(?:[a-zA-Z0-9\-_]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s<>'\"`(){}[\]]*)?",
    re.IGNORECASE,
)


def extract_volume_number(text: str) -> float | None:
    """Extrae el número de volumen del texto."""
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
    """Extrae candidatos limpios de título desde el mensaje."""
    first_line = text.strip().split("\n")[0]
    first_line = re.sub(r"^epub\s+de:\s*", "", first_line, flags=re.IGNORECASE)
    parts = re.split(r"[║|]", first_line)
    
    candidates = []
    for part in parts:
        cleaned = re.sub(r"[-─—]?\s*(?:volumen|vol|volume|v|tomo)\s*[\.\-:]?\s*\d+(?:\.\d+)?.*$", "", part, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+epubs?.*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\[.*?\]", "", cleaned)  # Quitar [Fansub]
        cleaned = cleaned.strip(" -─—:.,")
        if len(cleaned) >= 3:
            candidates.append(cleaned)
            
    return candidates if candidates else [first_line.strip()]


def match_post_to_book(message: str, all_books: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Encuentra el libro en la base de datos usando similitud de título y volumen."""
    vol_in_post = extract_volume_number(message)
    title_candidates = clean_title_candidates(message)
    
    best_match = None
    best_score = 0
    
    for b in all_books:
        b_title = (b.get("title") or "").lower()
        b_series_es = (b.get("series_spanish") or "").lower()
        b_series_en = (b.get("series_english") or "").lower()
        b_vol = b.get("volume")
        
        # Validación estricta de volumen si ambos tienen
        if vol_in_post is not None and b_vol is not None:
            try:
                if float(b_vol) != float(vol_in_post):
                    continue
            except ValueError:
                continue
                
        for cand in title_candidates:
            cand_low = cand.lower()
            if len(cand_low) < 4:
                continue
                
            score = 0
            if cand_low == b_title or cand_low == b_series_es or cand_low == b_series_en:
                score = 100
            elif cand_low in b_title or b_title in cand_low:
                score = 85
            elif cand_low in b_series_es or b_series_es in cand_low:
                score = 80
            elif cand_low in b_series_en or b_series_en in cand_low:
                score = 75
                
            # Si coincide volumen y título
            if score >= 75 and vol_in_post is not None:
                score += 10
                
            if score > best_score:
                best_score = score
                best_match = b
                
    if best_score >= 80:
        return best_match
    return None


async def run_full_simulation():
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
                "book_hash": b.book_hash,
            }
            for b in raw_books
            if b.short_link
        ]
        
    logger.info(f"✅ Libros cargados en memoria con short_link: {len(all_books)}")
    
    # Descargar todas las publicaciones de Facebook directamente
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
            
    logger.info(f"📄 Total de publicaciones descargadas de Facebook: {len(all_posts)}")
    
    matched_results = []
    unmatched_results = []
    
    for p in all_posts:
        msg = p.get("message") or ""
        urls = URL_REGEX.findall(msg)
        download_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        
        if not download_urls:
            continue
            
        matched_book = match_post_to_book(msg, all_books)
        if matched_book:
            new_url = f"https://dl.zeepubs.com/{matched_book['short_link']}"
            matched_results.append({
                "post_id": p.get("id"),
                "created_time": p.get("created_time"),
                "permalink_url": p.get("permalink_url"),
                "old_urls": download_urls,
                "new_url": new_url,
                "book_title": matched_book["title"],
                "book_volume": matched_book["volume"],
                "short_link": matched_book["short_link"],
            })
        else:
            unmatched_results.append({
                "post_id": p.get("id"),
                "created_time": p.get("created_time"),
                "permalink_url": p.get("permalink_url"),
                "old_urls": download_urls,
                "message_preview": msg[:140].replace("\n", " "),
            })
            
    # Guardar reporte de simulación
    output_data = {
        "summary": {
            "total_posts": len(all_posts),
            "posts_with_download_links": len(matched_results) + len(unmatched_results),
            "matched_posts_ready_to_update": len(matched_results),
            "unmatched_posts": len(unmatched_results),
        },
        "ready_to_update": matched_results,
        "unmatched": unmatched_results,
    }
    
    sim_file = Path("data/facebook_full_replacement_simulation.json")
    with open(sim_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Reporte completo guardado en: {sim_file.resolve()}")
    
    print("\n" + "=" * 75)
    print("📊 RESULTADOS GLOBALES DE LA SIMULACIÓN MASIVA (DRY-RUN)")
    print("=" * 75)
    print(f"Total publicaciones en Facebook:              {len(all_posts)}")
    print(f"Publicaciones con enlaces de descarga:         {len(matched_results) + len(unmatched_results)}")
    print(f"✅ Listas para actualizar automáticamente:     {len(matched_results)}")
    print(f"⚠️  Publicaciones sin coincidencia automática:   {len(unmatched_results)}")
    print("=" * 75)
    
    print("\n📋 PRIMERAS 10 SUSTITUCIONES PREPARADAS PARA EJECUTAR:")
    print("-" * 75)
    for i, r in enumerate(matched_results[:10], 1):
        print(f"[{i}] Libro BD: {r['book_title']} (Vol: {r['book_volume']})")
        print(f"    Post FB:    {r['permalink_url']}")
        print(f"    Anterior:   {r['old_urls'][0]}")
        print(f"    Nuevo Link: {r['new_url']}")
        print("-" * 75)


if __name__ == "__main__":
    asyncio.run(run_full_simulation())
