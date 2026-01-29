import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from config.config_settings import config

if "db:5432" in config.DATABASE_URL:
    config.DATABASE_URL = config.DATABASE_URL.replace("db:5432", "localhost:5432")

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook


async def find_resan_id():
    async with pg_manager.get_session() as session:
        res = await session.execute(
            select(LocalBook).where(LocalBook.title.ilike("%Byōsoku Go Senchimētoru%"))
        )
        b = res.scalar_one_or_none()
        if b:
            print(f"ID for {b.title}: {b.id}")
        else:
            print("Book not found")


if __name__ == "__main__":
    asyncio.run(find_resan_id())
