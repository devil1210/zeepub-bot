import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata


async def check():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        books = await s.execute(select(LocalBook))
        series = await s.execute(select(SeriesMetadata))
        print(f"Books in DB: {len(books.scalars().all())}")
        print(f"Series in DB: {len(series.scalars().all())}")
    await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check())
