#!/usr/bin/env python3
"""
Facebook Posts Links Replacement Engine (Fase 3: Dry-Run & Live)
Mapea publicaciones de Facebook con la base de datos de libros de ZeePub
para reemplazar enlaces antiguos de descarga (1drv.ms, onedrive, mega, mediafire, drive)
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
        r"(?:volumen|vol|volume|v)\s*[\.\-:]?\s*(\d+(?:\.\d+)?)",
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


def clean_title_for_search(text: str) -> str:
    """Limpia el texto del post para extraer el título de la novela."""
    first_line = text.strip().split("\n")[0]
    
    # Quitar prefijos comunes
    first_line = re.sub(r"^epub\s+de:\s*", "", first_line, flags=re.IGNORECASE)
    
    # Separar si tiene múltiples títulos con separador ║ o |
    parts = re.split(r"[║|]", first_line)
    
    candidates = []
    for part in parts:
        # Quitar volumen del nombre
        cleaned = re.sub(r"[-─—]?\s*(?:volumen|vol|volume|v|tomo)\s*[\.\-:]?\s*\d+(?:\.\d+)?.*$", "", part, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+epubs?.*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip(" -─—:.,")
        if len(cleaned) >= 3:
            candidates.append(cleaned)
            
    return candidates if candidates else [first_line.strip()]


async def match_post_to_book(message: str, all_books: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Encuentra el libro correspondiente en la base de datos usando similitud de título y volumen."""
    vol_in_post = extract_volume_number(message)
    title_candidates = clean_title_for_search(message)
    
    best_match = None
    best_score = 0
    
    for b in all_books:
        b_title = (b.get("title") or "").lower()
        b_series_es = (b.get("series_spanish") or "").lower()
        b_series_en = (b.get("series_english") or "").lower()
        b_vol = b.get("volume")
        
        # Coincidencia de volumen (si ambos tienen volumen)
        vol_match = True
        if vol_in_post is not None and b_vol is not None:
            try:
                vol_match = float(b_vol) == float(vol_in_post)
            except ValueError:
                vol_match = False
                
        if not vol_match and vol_in_post is not None:
            continue
            
        for cand in title_candidates:
            cand_low = cand.lower()
            if len(cand_low) < 4:
                continue
                
            # Exact match o substring
            score = 0
            if cand_low == b_title or cand_low == b_series_es or cand_low == b_series_en:
                score = 100
            elif cand_low in b_title or b_title in cand_low:
                score = 80
            elif cand_low in b_series_es or b_series_es in cand_low:
                score = 75
            elif cand_low in b_series_en or b_series_en in cand_low:
                score = 70
                
            if score > best_score:
                best_score = score
                best_match = b
                
    if best_score >= 70:
        return best_match
    return None


async def run_simulation(dry_run: bool = True):
    from core.db_manager_pg import pg_manager
    from models.communications import PublicationChannel
    from models.library import LocalBook

    await pg_manager.initialize()
    
    # 1. Cargar libros de la BD
    logger.info("📚 Cargando libros desde la base de datos...")
    async with pg_manager.get_session() as session:
        # Obtener canal oficial
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
    
    # 2. Cargar reporte de auditoría de Facebook
    report_file = Path("data/facebook_links_audit_report.json")
    if not report_file.exists():
        logger.error("❌ No existe el reporte facebook_links_audit_report.json. Ejecuta primero la auditoría.")
        return
        
    with open(report_file, "r", encoding="utf-8") as f:
        report_data = json.load(f)
        
    posts = report_data.get("broken_posts_details", [])
    logger.info(f"🔍 Evaluando {len(posts)} publicaciones con posibles links a actualizar...")
    
    simulation_results = []
    matched_count = 0
    skipped_count = 0
    
    for p in posts:
        post_id = p.get("post_id")
        created_time = p.get("created_time")
        permalink_url = p.get("permalink_url")
        
        # Obtener mensaje completo
        broken_links = [b.get("url") for b in p.get("broken_links", [])]
        download_links = [u for u in broken_links if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        
        if not download_links:
            skipped_count += 1
            continue
            
        # Intentar match con BD
        snippet = p.get("message_snippet", "")
        matched_book = await match_post_to_book(snippet, all_books)
        
        if matched_book:
            new_short_link = f"https://dl.zeepubs.com/{matched_book['short_link']}"
            simulation_results.append({
                "post_id": post_id,
                "created_time": created_time,
                "permalink_url": permalink_url,
                "old_download_urls": download_links,
                "matched_book_title": matched_book["title"],
                "matched_book_vol": matched_book["volume"],
                "new_download_url": new_short_link,
                "status": "MATCHED",
            })
            matched_count += 1
        else:
            simulation_results.append({
                "post_id": post_id,
                "created_time": created_time,
                "permalink_url": permalink_url,
                "old_download_urls": download_links,
                "matched_book_title": None,
                "matched_book_vol": None,
                "new_download_url": None,
                "status": "NO_MATCH",
            })
            skipped_count += 1
            
    # Guardar resultados de simulación
    sim_file = Path("data/facebook_links_replacement_simulation.json")
    with open(sim_file, "w", encoding="utf-8") as f:
        json.dump(simulation_results, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Reporte de simulación guardado en: {sim_file.resolve()}")
    
    print("\n" + "=" * 70)
    print("📊 RESULTADOS DE LA SIMULACIÓN MASIVA (DRY-RUN)")
    print("=" * 70)
    print(f"Total posts analizados con enlaces de descarga: {len(simulation_results)}")
    print(f"✅ Coincidencias exactas con libros en tu BD:   {matched_count}")
    print(f"⚠️  Posts sin coincidencia directa automática:     {skipped_count}")
    print("=" * 70)
    
    print("\n🔍 EJEMPLOS DE SUSTITUCIONES PREPARADAS:")
    print("-" * 70)
    shown = 0
    for r in simulation_results:
        if r["status"] == "MATCHED" and shown < 5:
            print(f"📌 Post: {r['permalink_url']}")
            print(f"   Fecha: {r['created_time']}")
            print(f"   Libro BD: {r['matched_book_title']} (Vol: {r['matched_book_vol']})")
            print(f"   Link Anterior: {r['old_download_urls'][0]}")
            print(f"   Nuevo Link:    {r['new_download_url']}")
            print("-" * 70)
            shown += 1


if __name__ == "__main__":
    asyncio.run(run_simulation())
