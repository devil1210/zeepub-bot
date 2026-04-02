
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        res = await conn.execute(text("SELECT * FROM bot_settings"))
        print("--- BOT SETTINGS ---")
        for row in res:
            print(row)
        
        # Check if there are other publication related tables
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [r[0] for r in res]
        print(f"--- TABLES --- \n{tables}")

if __name__ == "__main__":
    asyncio.run(check())
