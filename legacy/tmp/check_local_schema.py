import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db_manager_pg import pg_manager
from sqlalchemy import text

async def check_schema():
    await pg_manager.initialize()
    async with pg_manager.engine.connect() as conn:
        for table in ['series_metadata', 'local_books']:
            result = await conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"))
            columns = result.fetchall()
            print(f"Columns in {table}:")
            for col in columns:
                print(f" - {col[0]}: {col[1]}")
    await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(check_schema())
