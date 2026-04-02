import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv
from sqlalchemy import text

from core.db_manager_pg import pg_manager

load_dotenv()


async def check_schema():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    try:
        await pg_manager.initialize()
        async with pg_manager.engine.connect() as conn:
            # Check local_books columns
            res = await conn.execute(
                text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'local_books'
                AND column_name IN ('filepath', 'filename', 'title', 'series');
            """)
            )
            print("--- Table: local_books ---")
            for row in res:
                print(f"Column: {row[0]}, Type: {row[1]}, Length: {row[2]}")

            # Check series_metadata
            res = await conn.execute(
                text("""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = 'series_metadata'
                AND column_name IN ('slug', 'series_english', 'series_name');
            """)
            )
            print("\n--- Table: series_metadata ---")
            for row in res:
                print(f"Column: {row[0]}, Type: {row[1]}, Length: {row[2]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check_schema())
