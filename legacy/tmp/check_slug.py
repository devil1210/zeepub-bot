import asyncio
import sys
import logging

sys.path.append('.')
from core.db_manager_pg import pg_manager
pg_manager.db_url = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/zeepub"

from models.library import SeriesMetadata
from sqlalchemy import select

async def main():
    async with pg_manager.get_session() as session:
        # Search for the book
        res = await session.execute(select(SeriesMetadata).where(SeriesMetadata.series_name.ilike('%Maou ni Natta%')))
        for s in res.scalars().all():
            print(f'Name: {s.series_name}')
            print(f'English: {s.series_english}')
            print(f'Spanish: {s.series_spanish}')
            print(f'Slug: {s.slug}')
            print("---")
            
        res2 = await session.execute(select(SeriesMetadata).where(SeriesMetadata.series_name.ilike('%I Became the Demon Lord so I%')))
        for s in res2.scalars().all():
            print(f'Name2: {s.series_name}')
            print(f'English2: {s.series_english}')
            print(f'Spanish2: {s.series_spanish}')
            print(f'Slug2: {s.slug}')
            print("---")
            
asyncio.run(main())
