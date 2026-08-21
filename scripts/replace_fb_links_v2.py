#!/usr/bin/env python3
"""
Facebook Posts Links Replacement Engine (Fase 3 Refinada: Multi-versión, Color/B&N, Maquetador y Fansub)
Valida estrictamente:
1. Título y Volumen
2. Modo de Color (B&N / Blanco y Negro vs Color) por contexto de cada link
3. Maquetador (#Yayo, #Zhi, #Diego, #Zack, #Anghelgg, etc.)
4. Traductor / Fansub ([MK & LnF], Tamashi's, Onigiri, Kyuden, etc.)
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fb_replace_v2")

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
            
    return candidates if candidates else [first_line.strip()]


def extract_layout_and_fansubs(text: str) -> tuple[list[str], list[str]]:
    """Extrae maquetadores (#Hashtags) y nombres de fansub/traductor."""
    hashtags = re.findall(r"#([a-zA-Z0-9_]+)", text)
    # Filtrar hashtags comunes que no son nombres de personas
    layout_names = [
        h for h in hashtags
        if h.lower() not in ("zeepub", "zeepubs", "novela", "novelas", "epub", "anime", "nl", "novelaligera")
    ]
    
    # Buscar fansubs entre corchetes ej. [Dark Guild Fansub] o [MK & LnF]
    brackets = re.findall(r"\[(.*?)\]", text)
    fansubs = [b for b in brackets if not b.lower().startswith("epub")]
    
    return layout_names, fansubs


def detect_color_mode_context(message: str, url: str) -> str | None:
    """Determina si la URL específica en el post corresponde a Color o B&N."""
    # Buscar hasta 120 caracteres antes de la URL
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
    """Encuentra el libro exacto que coincide con una URL específica dentro del post."""
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
            elif (url_color_mode == "bw" and "[b&n]" in b_filename) or (url_color_mode == "color" and "[color]" in b_filename):
                score += 30
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
        
    # Ordenar por mayor puntuación
    candidates_books.sort(key=lambda x: x[0], reverse=True)
    best_score, best_book = candidates_books[0]
    
    if best_score >= 80:
        return best_book
    return None


async def run_refined_simulation():
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
        
    logger.info(f"✅ Libros cargados en memoria con short_link: {len(all_books)}")
    
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
    
    detailed_replacements = []
    unmatched_posts = []
    
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
                    "book_volume": matched_book["volume"],
                    "color_mode": matched_book["color_mode"],
                    "layout_by": matched_book["layout_by"],
                    "filename": matched_book["filename"],
                })
            else:
                post_replacements.append({
                    "old_url": dl_url,
                    "new_url": None,
                    "error": "No match found",
                })
                
        # Verificar si todos los links del post se pudieron resolver
        all_resolved = all(r.get("new_url") is not None for r in post_replacements)
        
        if all_resolved:
            detailed_replacements.append({
                "post_id": p.get("id"),
                "created_time": p.get("created_time"),
                "permalink_url": p.get("permalink_url"),
                "replacements": post_replacements,
                "multi_link": len(post_replacements) > 1,
            })
        else:
            unmatched_posts.append({
                "post_id": p.get("id"),
                "created_time": p.get("created_time"),
                "permalink_url": p.get("permalink_url"),
                "replacements": post_replacements,
                "message_preview": msg[:120].replace("\n", " "),
            })
            
    # Guardar reporte de simulación
    sim_output = {
        "summary": {
            "total_posts": len(all_posts),
            "posts_with_download_links": len(detailed_replacements) + len(unmatched_posts),
            "fully_matched_posts": len(detailed_replacements),
            "multi_link_posts": len([p for p in detailed_replacements if p["multi_link"]]),
            "unmatched_posts": len(unmatched_posts),
        },
        "ready_to_update": detailed_replacements,
        "unmatched": unmatched_posts,
    }
    
    sim_file = Path("data/facebook_refined_replacement_simulation.json")
    sim_file.parent.mkdir(parents=True, exist_ok=True)
    with open(sim_file, "w", encoding="utf-8") as f:
        json.dump(sim_output, f, ensure_ascii=False, indent=2)
        
    print("\n" + "=" * 75)
    print("📊 RESULTADOS DE LA SIMULACIÓN REFINADA (MULTI-VERSIÓN / COLOR & B&N)")
    print("=" * 75)
    print(f"Total publicaciones en Facebook:                   {len(all_posts)}")
    print(f"Publicaciones con enlaces de descarga:              {len(detailed_replacements) + len(unmatched_posts)}")
    print(f"✅ Publicaciones 100% resueltas con variante exacta: {len(detailed_replacements)}")
    print(f"   └── De las cuales tienen múltiples versiones:   {len([p for p in detailed_replacements if p['multi_link']])}")
    print(f"⚠️  Publicaciones no resueltas:                     {len(unmatched_posts)}")
    print("=" * 75)
    
    print("\n🔍 CASOS ESPECIALES MULTI-LINK (COLOR vs B&N) RESUELTOS CON PRECISIÓN:")
    print("-" * 75)
    multi_samples = [p for p in detailed_replacements if p["multi_link"]][:3]
    for p in multi_samples:
        print(f"📌 Post: {p['permalink_url']}")
        print(f"   Fecha: {p['created_time']}")
        for rep in p["replacements"]:
            print(f"   • Variante: [{rep['color_mode'].upper()}] - {rep['filename']}")
            print(f"     Anterior: {rep['old_url']}")
            print(f"     Nuevo:    {rep['new_url']}")
        print("-" * 75)


if __name__ == "__main__":
    asyncio.run(run_refined_simulation())
