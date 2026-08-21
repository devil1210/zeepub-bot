import asyncio
import httpx
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel
from sqlalchemy import select

async def inspect_post_structure():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        ch = (await s.execute(select(PublicationChannel).where(PublicationChannel.id == 6))).scalar_one_or_none()
        p_token = ch.config.get("page_access_token")
        
        async with httpx.AsyncClient() as client:
            # 1. Post de Junna
            r1 = await client.get(
                "https://graph.facebook.com/v19.0/109113064138279_1574533754371694",
                params={"access_token": p_token, "fields": "id,status_type,attachments{media_type,type,url,title,subattachments},is_hidden,timeline_visibility"},
            )
            print("Junna Post Data:", r1.json())
            
            # 2. Post de ¡Buenas, gente!
            r2 = await client.get(
                "https://graph.facebook.com/v19.0/109113064138279_1573677194457350",
                params={"access_token": p_token, "fields": "id,status_type,attachments{media_type,type,url,title,subattachments},is_hidden,timeline_visibility"},
            )
            print("Buenas Gente Post Data:", r2.json())

asyncio.run(inspect_post_structure())
