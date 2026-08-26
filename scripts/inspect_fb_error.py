import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.communications import PublicationChannel

async def test_single():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        res = await session.execute(select(PublicationChannel).where(PublicationChannel.id == 6))
        chan = res.scalar_one_or_none()
        token = chan.config.get('page_access_token')

    async with httpx.AsyncClient() as client:
        # Consultar información del post primero
        get_res = await client.get(
            'https://graph.facebook.com/v21.0/109113064138279_309113084138275',
            params={'access_token': token, 'fields': 'id,message,status_type,is_published,attachments'}
        )
        print('GET STATUS:', get_res.status_code)
        print('GET DATA:', get_res.json())

if __name__ == '__main__':
    asyncio.run(test_single())
