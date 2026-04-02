
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def debug_settings():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        print("Checking app_settings...")
        res = await conn.execute(text("SELECT key, value FROM app_settings"))
        cols = res.fetchall()
        for col in cols:
            print(f"- {col[0]} ({col[1]})")

if __name__ == "__main__":
    asyncio.run(debug_settings())
