import asyncio
import os
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def diagnose():
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            for table in ['user_ratings', 'user_downloads', 'media_assets']:
                res_cols = await session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
                cols = [row[0] for row in res_cols]
                print(f"COLUMNS_{table}: {','.join(cols)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
