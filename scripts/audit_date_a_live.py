import asyncio
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select, or_
from core.db_manager_pg import pg_manager
from models.communications import BookPublication
from models.library import Book

async def audit_date_a_live():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # 1. Buscar todos los libros de Date A Live en la base de datos
        stmt = select(Book).where(
            or_(
                Book.title.ilike("%Date A Live%"),
                Book.series_spanish.ilike("%Date A Live%"),
                Book.series_english.ilike("%Date A Live%"),
                Book.filepath.ilike("%Date A Live%"),
                Book.filename.ilike("%Date A Live%"),
                Book.title.ilike("%Date A Bullet%"),
                Book.series_spanish.ilike("%Date A Bullet%"),
                Book.series_english.ilike("%Date A Bullet%"),
                Book.filepath.ilike("%Date A Bullet%"),
                Book.filename.ilike("%Date A Bullet%")
            )
        ).order_by(Book.volume)
        
        res = await session.execute(stmt)
        books = res.scalars().all()
        print(f"=== LIBROS DE DATE A LIVE EN DB: {len(books)} ===")
        for b in books:
            import os
            exists = os.path.exists(b.filepath) if b.filepath else False
            print(f"ID: {b.id[:10]}... | Vol: {b.volume} | Short: {b.short_link} | Exists: {exists} | File: {b.filename}")

        # 2. Buscar todas las publicaciones de Date A Live
        pub_stmt = select(BookPublication).where(
            or_(
                BookPublication.caption.ilike("%Date A Live%"),
                BookPublication.caption.ilike("%Date A Bullet%")
            )
        )
        res_pubs = await session.execute(pub_stmt)
        pubs = res_pubs.scalars().all()
        print(f"\n=== PUBLICACIONES REGISTRADAS EN DB: {len(pubs)} ===")
        
        extracted_links = {}
        for p in pubs:
            if not p.caption:
                continue
            matches = re.findall(r"dl\.zeepubs\.com/([a-zA-Z0-9_-]+)", p.caption)
            for m in matches:
                first_line = p.caption.split("\n")[0] if p.caption else ""
                vol_match = re.search(r"Volumen\s*(\d+(?:\.\d+)?)", p.caption, re.I)
                vol = vol_match.group(1) if vol_match else "?"
                extracted_links[m] = {
                    "hash": m,
                    "platform": p.platform,
                    "post_id": p.post_id,
                    "vol": vol,
                    "first_line": first_line,
                    "pub_book_id": p.book_id
                }

        # 3. También buscar directamente en el feed de Facebook por si hay posts que no están en book_publications
        from models.communications import PublicationChannel
        res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res_chan.scalar_one_or_none()
        if chan:
            token = chan.config.get('page_access_token')
            page_id = str(chan.target_id)
            url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
            params = {'access_token': token, 'fields': 'id,message,created_time,permalink_url', 'limit': '100'}
            all_fb_posts = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                while url and len(all_fb_posts) < 700:
                    r = await client.get(url, params=params if len(all_fb_posts) == 0 else None)
                    if r.status_code != 200:
                        break
                    data = r.json()
                    all_fb_posts.extend(data.get('data', []))
                    url = data.get('paging', {}).get('next')
                    params = None

            print(f"Total posts descargados de FB: {len(all_fb_posts)}")
            for fbp in all_fb_posts:
                msg = fbp.get('message', '')
                if "date a live" in msg.lower() or "date a bullet" in msg.lower():
                    matches = re.findall(r"dl\.zeepubs\.com/([a-zA-Z0-9_-]+)", msg)
                    first_line = msg.split("\n")[0]
                    vol_match = re.search(r"Volumen\s*(\d+(?:\.\d+)?)", msg, re.I)
                    vol = vol_match.group(1) if vol_match else "?"
                    for m in matches:
                        if m not in extracted_links:
                            extracted_links[m] = {
                                "hash": m,
                                "platform": "facebook_direct",
                                "post_id": fbp.get('id'),
                                "vol": vol,
                                "first_line": first_line,
                                "pub_book_id": None
                            }

        print(f"\n=== TOTAL ENLACES ENCONTRADOS PARA PROBAR: {len(extracted_links)} ===")
        # 4. Probar cada enlace contra el endpoint local o dl.zeepubs.com
        async with httpx.AsyncClient(timeout=10.0) as test_client:
            for h, info in sorted(extracted_links.items(), key=lambda x: str(x[1].get('vol', '0'))):
                test_url = f"https://dl.zeepubs.com/{h}"
                try:
                    resp = await test_client.get(test_url, follow_redirects=False)
                    status = resp.status_code
                    is_ok = (status == 200)
                    cd = resp.headers.get("content-disposition", "")
                    filename = cd.split("filename=")[-1] if cd else ""
                    print(f"[{status}] {test_url} | Vol: {info['vol']} | OK: {is_ok} | Header: {info['first_line'][:40]} | File: {filename}")
                except Exception as ex:
                    print(f"[ERR] {test_url} | Vol: {info['vol']} | Error: {ex}")

if __name__ == "__main__":
    asyncio.run(audit_date_a_live())
