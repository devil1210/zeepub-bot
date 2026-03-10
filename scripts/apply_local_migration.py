import asyncio
import logging
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.getcwd())

from config.config_settings import config  # noqa: E402

# Patch DATABASE_URL to use localhost for local migration
if "db:5432" in config.DATABASE_URL:
    config.DATABASE_URL = config.DATABASE_URL.replace("db:5432", "localhost:5432")

from sqlalchemy import text  # noqa: E402

from core.db_manager_pg import pg_manager  # noqa: E402


async def apply_local_migration():
    commands = [
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS word_count integer",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS page_count integer",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS reading_time integer",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS epub_version text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS isbn text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS asin text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS layout_by text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS publisher text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS spanish_title text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS romaji_title text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS english_title text",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS is_uncensored integer",
        "ALTER TABLE books ADD COLUMN IF NOT EXISTS color_mode text",
    ]

    logger.info("Applying migration to local database (localhost:5432)...")
    try:
        async with pg_manager.get_session() as session:
            for cmd in commands:
                await session.execute(text(cmd))
            await session.commit()
            logger.info("✅ Local migration successful.")
    except Exception as e:
        logger.error(f"❌ Local migration failed: {e}")


if __name__ == "__main__":
    asyncio.run(apply_local_migration())
