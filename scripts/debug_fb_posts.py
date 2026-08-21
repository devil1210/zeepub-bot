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
                params={"access_token": token, "fields": "id,message,created_time", "limit": "20"},
            )
            print("Status:", resp.status_code)
            data = resp.json()
            posts = data.get("data", [])
            print(f"Posts obtenidos: {len(posts)}")
            for i, p in enumerate(posts[:5]):
                print(f"[{i+1}] ID: {p.get('id')} | Msg: {repr(p.get('message'))[:80]}")

asyncio.run(inspect())
