
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def fix():
    await pg_manager.initialize()
    async with pg_manager.engine.begin() as conn:
        print("Ensuring columns exist...")
        await conn.execute(text("ALTER TABLE discovered_chats ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
        await conn.execute(text("ALTER TABLE discovered_chats ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
        print("Success.")

if __name__ == "__main__":
    asyncio.run(fix())
