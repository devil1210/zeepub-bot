import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.curdir))

from core.db_manager_pg import pg_manager
from sqlalchemy import text

async def check_pgvector():
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';"))
            exists = result.scalar()
            print(f"pgvector extension: {'FOUND' if exists == 'vector' else 'NOT FOUND'}")
            
            if exists != 'vector':
                print("Attempting to enable pgvector (requires superuser)...")
                # Using session.execute with CREATE EXTENSION might fail if not superuser
                await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                # Commit is handled by pg_manager.get_session context
                print("pgvector enabled successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(check_pgvector())
