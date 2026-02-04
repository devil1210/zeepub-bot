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


async def find_resan():
    async with pg_manager.get_session() as session:
        res = await session.execute(select(LocalBook).where(LocalBook.layout_by.ilike("%Resan%")))
        books = res.scalars().all()

        print(f"Checking {len(books)} books by Resan:")
        for b in books:
            size_mb = round(b.file_size / (1024 * 1024), 2) if b.file_size else 0
            if size_mb == 4.29:
                print(f"MATCH FOUND: {b.title}")
                print(f"  Words: {b.word_count}")
                print(f"  Pages: {b.page_count}")
                print(f"  Size: {size_mb} MB ({b.file_size} bytes)")
            # else:
            #     print(f"Other: {b.title} ({size_mb} MB)")


if __name__ == "__main__":
    asyncio.run(find_resan())
