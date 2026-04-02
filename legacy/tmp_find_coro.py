import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.curdir))
from core.db_manager_pg import pg_manager
from models.library import Series
from sqlalchemy import select

async def check():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        result = await session.execute(select(Series).limit(1))
        series = result.scalar_one_or_none()
        if series:
            d = series.to_dict()
            for k, v in d.items():
                if asyncio.iscoroutine(v):
                    print(f"COROUTINE FOUND: {k}")
                else:
                    print(f"{k}: {type(v)}")

asyncio.run(check())
