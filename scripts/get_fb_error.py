import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from sqlalchemy import select

async def get_err():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.platform == "facebook"))).scalars().first()
        token = ch.config.get("access_token") or ch.config.get("page_access_token")
        page_id = ch.target_id
        async with httpx.AsyncClient() as c:
            r = await c.get(f"https://graph.facebook.com/v21.0/{page_id}/published_posts", params={"access_token": token})
            print("Error FB:", r.status_code, r.text)

asyncio.run(get_err())
