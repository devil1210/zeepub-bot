import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def diagnose():
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            res = await session.execute(text("SELECT column_name, is_nullable, column_default FROM information_schema.columns WHERE table_name = 'series'"))
            cols = res.fetchall()
            for col in cols:
                print(f"COL: {col[0]} | NULLABLE: {col[1]} | DEFAULT: {col[2]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
