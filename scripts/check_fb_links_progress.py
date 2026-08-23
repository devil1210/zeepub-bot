import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import re
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from models.library import LocalBook
from scripts.execute_fb_replace_batch import DOWNLOAD_DOMAINS, URL_REGEX

async def main():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res_chan = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res_chan.scalar_one_or_none()
        if not chan:
            print("ERROR: No channel 6")
            return
        page_id = str(chan.target_id)
        token = chan.config.get('page_access_token')

    url = f"https://graph.facebook.com/v21.0/{page_id}/published_posts"
    params = {'access_token': token, 'fields': 'id,message,created_time,permalink_url', 'limit': '100'}
    all_posts = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            resp = await client.get(url, params=params if len(all_posts) == 0 else None)
            if resp.status_code != 200:
                print("Error Graph API:", resp.status_code, resp.text)
                break
            data = resp.json()
            posts = data.get('data', [])
            all_posts.extend(posts)
            url = data.get('paging', {}).get('next')
            params = None

    already_zeepubs = 0
    pending_old_links = 0
    other_posts = 0

    for p in all_posts:
        msg = p.get('message') or ''
        urls = URL_REGEX.findall(msg)
        dl_urls = [u for u in urls if any(d in u.lower() for d in DOWNLOAD_DOMAINS)]
        if not dl_urls:
            if 'dl.zeepubs.com' in msg:
                already_zeepubs += 1
            else:
                other_posts += 1
        else:
            pending_old_links += 1

    print("--- REPORTE ESTADO LINKS FACEBOOK ---")
    print(f"Total Publicaciones en Feed: {len(all_posts)}")
    print(f"Publicaciones con link oficial (dl.zeepubs.com): {already_zeepubs}")
    print(f"Publicaciones con links antiguos pendientes (OneDrive/Drive/Mediafire/Mega): {pending_old_links}")
    print(f"Otras publicaciones informativas/sin links de descarga: {other_posts}")

if __name__ == "__main__":
    asyncio.run(main())
