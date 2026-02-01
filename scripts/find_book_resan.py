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


async def find_book():
    async with pg_manager.get_session() as session:
        # Search for maquetador 'Resan'
        res = await session.execute(
            select(LocalBook).where(LocalBook.layout_by.ilike("%Resan%"))
        )
        books = res.scalars().all()

        print(f"Found {len(books)} books by Resan:")
        for b in books:
            print(f"Title: {b.title}")
            print(f"  ID: {b.id}")
            print(f"  Words: {b.word_count}")
            print(f"  Pages: {b.page_count}")
            print(f"  Reading Time: {b.reading_time}")
            print(f"  Path: {b.filepath}")
            print("-" * 30)


if __name__ == "__main__":
    asyncio.run(find_book())
