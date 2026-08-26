import asyncio
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel, BookPublication
from models.library import LocalBook
from scripts.execute_fb_replace_batch import DOWNLOAD_DOMAINS, URL_REGEX, match_single_link

async def import_all_fb_publications():
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

    print(f"Total posts descargados de Facebook: {len(all_posts)}")
    
    records_to_insert = []
    matched_posts_count = 0

    for p in all_posts:
        msg = p.get('message') or ''
        urls = URL_REGEX.findall(msg)
        dl_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS) or "dl.zeepubs.com" in u.lower()]
        if not dl_urls:
            continue

        created_str = p.get('created_time')
        pub_date = None
        if created_str:
            try:
                # Convertir a datetime naive (UTC)
                dt_obj = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                pub_date = dt_obj.replace(tzinfo=None)
            except Exception:
                pub_date = datetime.utcnow()

        post_id = p.get('id')
        permalink = p.get('permalink_url') or f"https://www.facebook.com/{post_id}"

        post_books_seen = set()
        for dl in dl_urls:
            matched_book = None
            if "dl.zeepubs.com" in dl:
                s_code = dl.split("/")[-1].strip()
                matched_book = next((b for b in all_books if b.get("short_link") == s_code), None)
            
            if not matched_book:
                matched_book = match_single_link(msg, dl, all_books)

            if matched_book and matched_book["id"] not in post_books_seen:
                post_books_seen.add(matched_book["id"])
                records_to_insert.append({
                    "book_id": matched_book["id"],
                    "platform": "facebook",
                    "channel_id": 6,
                    "post_id": post_id,
                    "post_url": permalink,
                    "caption": msg,
                    "published_at": pub_date,
                })

        if post_books_seen:
            matched_posts_count += 1

    print(f"Vinculaciones encontradas: {len(records_to_insert)} registros para {matched_posts_count} posts.")

    # Guardar en base de datos
    async with pg_manager.get_session() as session:
        # Obtener primero los pares existentes
        existing_res = await session.execute(select(BookPublication.book_id, BookPublication.post_id))
        existing_pairs = set(existing_res.all())

        inserted_count = 0
        for rec in records_to_insert:
            if (rec["book_id"], rec["post_id"]) not in existing_pairs:
                pub = BookPublication(
                    book_id=rec["book_id"],
                    platform=rec["platform"],
                    channel_id=rec["channel_id"],
                    post_id=rec["post_id"],
                    post_url=rec["post_url"],
                    caption=rec["caption"],
                    published_at=rec["published_at"],
                )
                session.add(pub)
                existing_pairs.add((rec["book_id"], rec["post_id"]))
                inserted_count += 1
        
        await session.commit()

    print(f"🎉 Poblado finalizado con éxito: {inserted_count} publicaciones guardadas en la tabla book_publications.")

if __name__ == "__main__":
    asyncio.run(import_all_fb_publications())
