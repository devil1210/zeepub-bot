import asyncio
from sqlalchemy import select
from core.db_manager_pg import pg_manager
from models.library import SeriesMetadata

async def main():
    async with pg_manager.get_session() as session:
        res = await session.execute(select(SeriesMetadata).where(SeriesMetadata.series_name.ilike('%arifureta%')))
        print([s.series_name for s in res.scalars().all()])

asyncio.run(main())
