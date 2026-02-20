import asyncio
import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.getcwd())

from config.config_settings import config

# Patch DATABASE_URL IMMEDIATELY
if "db:5432" in config.DATABASE_URL:
    config.DATABASE_URL = config.DATABASE_URL.replace("db:5432", "localhost:5432")
    logger.info(f"🔄 Patching DB URL to: {config.DATABASE_URL}")

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook


async def inspect():
    try:
        async with pg_manager.get_session() as session:
            # Check a few books
            res = await session.execute(select(LocalBook).limit(10))
            books = res.scalars().all()

            if not books:
                print("❌ No books found in local_books table.")
                return

            print(f"\n--- Database Inspection ({len(books)} books) ---")
            for b in books:
                print(f"Title: {b.title}")
                print(f"  - Words: {b.word_count}")
                print(f"  - Pages: {b.page_count}")
                print(f"  - Reading Time: {b.reading_time}")
                print(f"  - File: {b.filepath}")
                print("-" * 30)

            # Count how many have 0 or None
            zeros_res = await session.execute(
                select(LocalBook).where((LocalBook.word_count == 0) | (LocalBook.word_count.is_(None)))
            )
            zeros_count = len(zeros_res.scalars().all())
            print(f"\nTotal books with missing/zero word_count: {zeros_count}")

    except Exception as e:
        logger.error(f"❌ Inspection failed: {e}")


if __name__ == "__main__":
    asyncio.run(inspect())
