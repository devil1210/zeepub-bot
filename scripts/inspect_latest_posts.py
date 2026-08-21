import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from sqlalchemy import select

async def inspect_published():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 6))).scalar_one_or_none()
        p_token = ch.config.get("page_access_token")
        page_id = ch.target_id
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://graph.facebook.com/v19.0/{page_id}/published_posts",
                params={"access_token": p_token, "limit": "5", "fields": "id,created_time,message,permalink_url"},
            )
            data = resp.json().get("data", [])
            print("ÚLTIMOS 5 POSTS EN PUBLISHED_POSTS:")
            for p in data:
                print("---")
                print("ID:", p.get("id"))
                print("Time:", p.get("created_time"))
                print("Link:", p.get("permalink_url"))
                print("Msg:", repr(p.get("message"))[:100])

asyncio.run(inspect_published())
