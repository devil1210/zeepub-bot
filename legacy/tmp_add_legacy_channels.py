import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
os.environ['DATABASE_URL'] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

from config.config_settings import config
config.DATABASE_URL = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

from core.db_manager_pg import pg_manager
from models.publication_models import PublicationChannel
from sqlalchemy import select

async def migrate_channels():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # Check existing
        result = await session.execute(select(PublicationChannel))
        existing_targets = [c.target_id for c in result.scalars().all()]
        
        channels_to_add = [
            {"name": "ZeePubs Principal", "target_id": "@ZeePubs"},
            {"name": "ZeePubs Test", "target_id": "@ZeePubBotTest"}
        ]
        
        changes = False
        for c in channels_to_add:
            if c["target_id"] not in existing_targets:
                new_c = PublicationChannel(
                    name=c["name"],
                    platform="telegram",
                    target_id=c["target_id"],
                    is_active=True,
                    is_favorite=True
                )
                session.add(new_c)
                print(f"Added channel: {c['name']} ({c['target_id']})")
                changes = True
        
        if changes:
            await session.commit()
    await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(migrate_channels())
