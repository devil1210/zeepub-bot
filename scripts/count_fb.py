import asyncio
from core.db_manager_pg import pg_manager
from models.library import Book
from sqlalchemy import select, func

async def check():
    await pg_manager.initialize()
    async with pg_manager.get_session() as s:
        total = (await s.execute(select(func.count(Book.id)))).scalar()
        with_fb = (await s.execute(select(func.count(Book.id)).where(Book.fb_post_id.isnot(None)))).scalar()
        print("RESULTADO_DB:", total, with_fb)

asyncio.run(check())
