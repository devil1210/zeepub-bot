import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel

async def test_comments():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res.scalar_one_or_none()
        token = chan.config.get('page_access_token')

    post_id = "109113064138279_309113084138275"
    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Probar crear un comentario oficial fijado en el post
        comment_msg = "📌 Enlace de descarga oficial actualizado (EPUB3):\nhttps://dl.zeepubs.com/zSb8UIZX3I"
        # POST /{post_id}/comments
        c_res = await client.post(
            f"https://graph.facebook.com/v21.0/{post_id}/comments",
            params={"access_token": token},
            data={"message": comment_msg}
        )
        print("POST COMMENT STATUS:", c_res.status_code)
        print("POST COMMENT DATA:", c_res.json())

if __name__ == "__main__":
    asyncio.run(test_comments())
