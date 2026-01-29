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


async def inspect():
    async with pg_manager.get_session() as session:
        res = await session.execute(select(LocalBook).limit(50))
        books = res.scalars().all()
        print(f"Inspecting {len(books)} books:")
        count_zero = 0
        for b in books:
            if not b.word_count:
                count_zero += 1
            print(f"- {b.title[:40]:<40} | W: {b.word_count} | P: {b.page_count}")
        print(f"\nTotal zero/None in sample: {count_zero}")


if __name__ == "__main__":
    asyncio.run(inspect())
