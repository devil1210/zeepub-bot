import asyncio
from core.db_manager_pg import pg_manager
from sqlalchemy import text

async def check():
    async with pg_manager.get_session() as session:
        for table in ['local_books', 'series_metadata', 'user_downloads']:
            res = await session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
            cols = [row[0] for row in res.fetchall()]
            print(f"{table} columns: {cols}")

if __name__ == "__main__":
    asyncio.run(check())
