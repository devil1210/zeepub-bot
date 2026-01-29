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


async def find_book_size():
    async with pg_manager.get_session() as session:
        # Search for size approx 4.29 MB
        # 4.29 * 1024 * 1024 = 4498391
        res = await session.execute(
            select(LocalBook).where(LocalBook.file_size >= 4400000, LocalBook.file_size <= 4600000)
        )
        books = res.scalars().all()

        print(f"Found {len(books)} books around 4.29 MB:")
        for b in books:
            if b.layout_by and "Resan" in b.layout_by:
                print(f"MATCH: {b.title}")
                print(f"  Words: {b.word_count}")
                print(f"  Pages: {b.page_count}")
                print(f"  Updated: {b.file_modified_at}")
            else:
                print(f"Skip: {b.title} (Maquetador: {b.layout_by})")


if __name__ == "__main__":
    asyncio.run(find_book_size())
