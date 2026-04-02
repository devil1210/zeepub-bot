
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [r[0] for r in res]
        print("TABLES_LIST_START")
        for t in tables:
            print(t)
        print("TABLES_LIST_END")

if __name__ == "__main__":
    asyncio.run(check())
