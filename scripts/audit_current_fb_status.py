import asyncio
import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel

async def inspect():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.platform == "facebook"))).scalars().first()
        token = ch.config.get("access_token") or ch.config.get("page_access_token")
        page_id = ch.target_id
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://graph.facebook.com/v21.0/{page_id}/published_posts",
                params={"access_token": token, "fields": "id,message,created_time", "limit": "100"},
            )
            posts = resp.json().get("data", [])
            with_old = 0
            with_new = 0
            for p in posts:
                msg = p.get("message", "")
                if "dl.zeepubs.com" in msg:
                    with_new += 1
                if any(d in msg for d in ["1drv.ms", "onedrive.live.com", "drive.google.com", "mediafire.com", "mega.nz"]):
                    with_old += 1
            print(f"MUESTRA RECIENTE (100 posts): Con dl.zeepubs.com: {with_new} | Con enlaces antiguos: {with_old}")

asyncio.run(inspect())
