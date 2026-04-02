import asyncio
import os
import sys
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager

async def main():
    try:
        async with pg_manager.get_session() as s:
            res = await s.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            for row in res.fetchall():
                print(row[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
