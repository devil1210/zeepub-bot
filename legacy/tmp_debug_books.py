
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def debug_books():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        print("Checking columns of books...")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'books'
        """))
        cols = res.fetchall()
        for col in cols:
            print(f"- {col[0]} ({col[1]})")

if __name__ == "__main__":
    asyncio.run(debug_books())
