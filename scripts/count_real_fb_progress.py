import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from sqlalchemy import select

async def count_progress():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 6))).scalar_one_or_none()
        p_token = ch.config.get("page_access_token")
        page_id = ch.target_id
        
        url = f"https://graph.facebook.com/v19.0/{page_id}/published_posts"
        params = {"access_token": p_token, "fields": "id,message,created_time", "limit": "100"}
        
        all_posts = []
        with_new = 0
        with_old = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while url and len(all_posts) < 600:
                resp = await client.get(url, params=params if len(all_posts) == 0 else None)
                if resp.status_code != 200:
                    print("Error paginacion:", resp.text)
                    break
                data = resp.json()
                posts = data.get("data", [])
                if not posts:
                    break
                all_posts.extend(posts)
                for p in posts:
                    msg = p.get("message", "")
                    if "dl.zeepubs.com" in msg:
                        with_new += 1
                    if any(d in msg for d in ["1drv.ms", "onedrive.live.com", "drive.google.com", "mediafire.com", "mega.nz"]):
                        with_old += 1
                url = data.get("paging", {}).get("next")
                
        print("="*60)
        print(f"TOTAL POSTS ANALIZADOS EN FACEBOOK: {len(all_posts)}")
        print(f"✅ YA ACTUALIZADOS (con dl.zeepubs.com): {with_new}")
        print(f"⏳ PENDIENTES CON ENLACES ANTIGUOS:     {with_old}")
        print("="*60)

asyncio.run(count_progress())
