import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from models.library import LocalBook
from scripts.execute_fb_replace_batch import DOWNLOAD_DOMAINS, URL_REGEX, match_single_link, clean_title_candidates, extract_volume_number

async def diagnose():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res_chan.scalar_one_or_none()
        page_id = str(chan.target_id)
        token = chan.config.get('page_access_token')

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

    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {'access_token': token, 'fields': 'id,message,created_time,permalink_url', 'limit': '100'}
    all_posts = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            resp = await client.get(url, params=params if len(all_posts) == 0 else None)
            if resp.status_code != 200: break
            data = resp.json()
            posts = data.get('data', [])
            all_posts.extend(posts)
            url = data.get('paging', {}).get('next')
            params = None

    print(f"Total posts descargados: {len(all_posts)}")
    unmatched = []

    for p in all_posts:
        msg = p.get('message') or ''
        urls = URL_REGEX.findall(msg)
        dl_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        if not dl_urls:
            continue

        failed = []
        for dl in dl_urls:
            matched = match_single_link(msg, dl, all_books)
            if not matched:
                failed.append(dl)

        if failed:
            first_line = msg.strip().split('\n')[0] if msg else ''
            unmatched.append({
                "post_id": p.get("id"),
                "first_line": first_line,
                "vol": extract_volume_number(msg),
                "candidates": clean_title_candidates(msg),
                "failed_links": failed
            })

    print(f"\n--- TOTAL PUBLICACIONES SIN MATCH EXACTO: {len(unmatched)} ---")
    for u in unmatched[:15]:
        print(f"Post ID: {u['post_id']}")
        print(f"  Header: {u['first_line']}")
        print(f"  Volumen extraído: {u['vol']}")
        print(f"  Candidatos de título: {u['candidates']}")
        print(f"  Links no resueltos: {u['failed_links']}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(diagnose())
