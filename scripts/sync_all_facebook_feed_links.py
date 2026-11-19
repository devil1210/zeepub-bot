import asyncio
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select, text
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from models.library import Book


def normalize_text(val: str | None) -> str:
    if not val:
        return ""
    val = val.replace("’", "'").replace("‘", "'").replace("“", "\"").replace("”", "\"")
    val = val.replace("–", "-").replace("—", "-")
    val = unicodedata.normalize("NFKD", val)
    val = "".join(c for c in val if not unicodedata.combining(c))
    return val.lower().strip()


def extract_title_candidates(message: str) -> list[str]:
    lines = [l.strip() for l in message.strip().split("\n") if l.strip()]
    if not lines:
        return []

    candidates = []
    first_line = lines[0]
    first_line = re.sub(r"^(?:epub\s+de:\s*|[📚📖]\s*)", "", first_line, flags=re.IGNORECASE)
    parts = re.split(r"[║|]", first_line)
    for p in parts:
        cleaned = re.sub(
            r"[-─—]?\s*(?:volumen|vol|volume|v|tomo)\s*[\.\-:]?\s*\d+(?:\.\d+)?.*$",
            "",
            p,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+epubs?.*$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\[.*?\]", "", cleaned)
        cleaned = cleaned.strip(" -─—:.,")
        if len(cleaned) >= 3:
            candidates.append(cleaned)

    return candidates


def extract_vol(message: str) -> float | None:
    m = re.search(
        r"(?:volumen|vol|volume|tomo|v)\s*[\.\-:]?\s*(\d+(?:\.\d+)?)",
        message,
        flags=re.IGNORECASE,
    )
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


async def auto_heal_all_facebook_links():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # 1. Cargar libros
        res_books = await session.execute(select(Book))
        books = res_books.scalars().all()
        books_by_short = {b.short_link: b for b in books if b.short_link}

        # Cargar mappings existentes
        res_maps = await session.execute(
            text("SELECT hash, url FROM url_mappings WHERE is_valid = true;")
        )
        existing_mappings = {r[0]: r[1] for r in res_maps.fetchall()}

        # 2. Descargar feed completo de Facebook
        res_chan = await session.execute(
            select(PublicationChannel).where(PublicationChannel.id == 6)
        )
        chan = res_chan.scalar_one_or_none()
        token = chan.config.get("page_access_token")
        page_id = str(chan.target_id)

        url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
        params = {
            "access_token": token,
            "fields": "id,message,created_time,permalink_url",
            "limit": "100",
        }
        all_posts = []

        async with httpx.AsyncClient(timeout=35.0) as client:
            while url:
                r = await client.get(url, params=params if len(all_posts) == 0 else None)
                if r.status_code != 200:
                    break
                data = r.json()
                posts = data.get("data", [])
                all_posts.extend(posts)
                url = data.get("paging", {}).get("next")
                params = None

        print(f"Total publicaciones descargadas de Facebook: {len(all_posts)}")

        healed_count = 0
        already_valid = 0
        unmatched_count = 0

        for p in all_posts:
            msg = p.get("message", "")
            if not msg:
                continue
            links = re.findall(r"dl\.zeepubs\.com/([a-zA-Z0-9_-]+)", msg)
            if not links:
                continue

            for h in links:
                # Si ya existe en books actual o en url_mappings, está ok
                if h in books_by_short or h in existing_mappings:
                    already_valid += 1
                    continue

                # Si no existe, buscar el libro que hace match de forma robusta
                vol = extract_vol(msg)
                cands = extract_title_candidates(msg)
                norm_cands = [normalize_text(c) for c in cands if len(normalize_text(c)) >= 3]

                matches = []
                for b in books:
                    if vol is not None and b.volume is not None:
                        if abs(b.volume - vol) > 0.01:
                            continue

                    b_titles = [
                        normalize_text(b.title),
                        normalize_text(b.series_spanish),
                        normalize_text(b.series_english),
                    ]
                    b_titles = [t for t in b_titles if len(t) >= 3]

                    score = 0
                    for c in norm_cands:
                        for bt in b_titles:
                            if c == bt:
                                score = max(score, 100)
                            elif len(c) >= 5 and len(bt) >= 5:
                                if c in bt or bt in c:
                                    score = max(score, 85)

                    if score >= 85:
                        matches.append((score, b))

                if matches:
                    matches.sort(key=lambda x: x[0], reverse=True)
                    best_match = matches[0][1]

                    if best_match.filepath:
                        ins_stmt = text("""
                            INSERT INTO url_mappings (hash, url, book_title, series_name, volume_number, is_valid)
                            VALUES (:hash, :url, :title, :series, :volume, true)
                            ON CONFLICT (hash) DO UPDATE SET
                                url = EXCLUDED.url,
                                book_title = EXCLUDED.book_title,
                                is_valid = true;
                        """)
                        await session.execute(
                            ins_stmt,
                            {
                                "hash": h,
                                "url": best_match.filepath,
                                "title": best_match.title,
                                "series": best_match.series_spanish
                                or best_match.series_english
                                or "",
                                "volume": str(best_match.volume)
                                if best_match.volume is not None
                                else "",
                            },
                        )
                        existing_mappings[h] = best_match.filepath
                        healed_count += 1
                        first_l = msg.strip().split("\n")[0]
                        print(
                            f"🩹 Auto-reparado hash '{h}' -> {best_match.title} (Vol {best_match.volume}) | {first_l[:40]}"
                        )
                else:
                    unmatched_count += 1
                    first_l = msg.strip().split("\n")[0]
                    print(f"⚠️ No se pudo emparejar: '{h}' | {first_l[:40]}")

        await session.commit()
        print(f"\n==================================================")
        print(f"📊 REPORTE DE AUTO-CURACIÓN GLOBAL:")
        print(f"   ✅ Enlaces que ya estaban válidos: {already_valid}")
        print(f"   🩹 Enlaces huérfanos reparados:    {healed_count}")
        print(f"   ⚠️ Enlaces sin coincidencia local: {unmatched_count}")
        print(f"==================================================")


if __name__ == "__main__":
    asyncio.run(auto_heal_all_facebook_links())
