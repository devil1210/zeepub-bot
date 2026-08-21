import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.library import Book
from models.communications import PublicationChannel
from sqlalchemy import select

async def inspect():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        b = (await s.execute(select(Book).where(Book.id == "32b3f612d59240acac67967a12bd0c662e09e416c925ef05cef761bb4bc5d0b6"))).scalar_one_or_none()
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 6))).scalar_one_or_none()
        p_token = ch.config.get("page_access_token")
        
        print("LIBRO:", b.title if b else None)
        print("FB_POST_ID:", b.fb_post_id if b else None)
        print("FB_PHOTO_ID:", b.fb_photo_id if b else None)
        
        if b and b.fb_post_id:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"https://graph.facebook.com/v19.0/{b.fb_post_id}", params={"access_token": p_token, "fields": "id,created_time,message,is_published,privacy,shares,permalink_url"})
                print("FB POST DATA:", r.status_code, r.text)

asyncio.run(inspect())
