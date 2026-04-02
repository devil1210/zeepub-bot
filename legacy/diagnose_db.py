import asyncio
import os
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def diagnose():
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            # List tables
            res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in res]
            print(f"Tables: {tables}")
            
            # Check 'series' and 'books' columns
            for table in ['series', 'series_metadata', 'books', 'local_books']:
                if table in tables:
                    res_cols = await session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'"))
                    cols = [row[0] for row in res_cols]
                    print(f"Columns in {table}: {cols}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())
