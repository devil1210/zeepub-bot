
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        for table in ["discovered_chats", "publication_channels", "download_logs", "user_downloads"]:
            try:
                res = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = res.scalar()
                print(f"Table {table}: {count} records")
            except Exception as e:
                print(f"Table {table}: Error {e}")

if __name__ == "__main__":
    asyncio.run(check())
