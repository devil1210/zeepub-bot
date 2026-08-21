import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from sqlalchemy import select

async def test_debug_token():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 6))).scalar_one_or_none()
        p_token = ch.config.get("page_access_token")
        page_id = ch.target_id
        
        async with httpx.AsyncClient() as client:
            # 1. Probar lectura de albums
            r_alb = await client.get(f"https://graph.facebook.com/v19.0/{page_id}/albums", params={"access_token": p_token, "limit": "5"})
            print("1. Lectura Albums (/albums):", r_alb.status_code, "Total:", len(r_alb.json().get("data", [])))
            
            # 2. Probar lectura de /feed
            r_feed = await client.get(f"https://graph.facebook.com/v19.0/{page_id}/feed", params={"access_token": p_token, "limit": "5"})
            print("2. Lectura Muro (/feed):", r_feed.status_code, r_feed.text[:120])
            
            # 3. Probar lectura de /published_posts
            r_posts = await client.get(f"https://graph.facebook.com/v19.0/{page_id}/published_posts", params={"access_token": p_token, "limit": "5"})
            print("3. Lectura (/published_posts):", r_posts.status_code, r_posts.text[:120])

asyncio.run(test_debug_token())
