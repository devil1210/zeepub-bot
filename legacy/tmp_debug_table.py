
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def debug_table():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        print("Checking columns of discovered_chats...")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'discovered_chats'
        """))
        cols = res.fetchall()
        for col in cols:
            print(f"- {col[0]} ({col[1]})")
        
        if not any(c[0] == 'updated_at' for c in cols):
             print("ALARM: updated_at is missing!")
             await conn.execute(text("ALTER TABLE discovered_chats ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
             print("Added updated_at manually.")

if __name__ == "__main__":
    asyncio.run(debug_table())
