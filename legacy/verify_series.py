
import asyncio
import os
import logging

os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

from core.db_manager_pg import pg_manager
from models.library import SeriesMetadata
from sqlalchemy import select

async def check():
    async with pg_manager.get_session() as session:
        stmt = select(SeriesMetadata).limit(10)
        series = (await session.execute(stmt)).scalars().all()
        print(f"✅ Series en la tabla ({len(series)} ejemplos):")
        for s in series:
            print(f" - {s.series_name} (ID: {s.id}, Hash: {s.series_hash[:8]}...)")

if __name__ == "__main__":
    asyncio.run(check())
