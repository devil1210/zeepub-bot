import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_theme_columns():
    queries = [
        "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS border_radius INTEGER DEFAULT 24;",
        "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS border_width INTEGER DEFAULT 1;",
        "ALTER TABLE user_ui_settings ADD COLUMN IF NOT EXISTS border_radius INTEGER;",
        "ALTER TABLE user_ui_settings ADD COLUMN IF NOT EXISTS border_width INTEGER;",
        "ALTER TABLE user_ui_settings ADD COLUMN IF NOT EXISTS glass_blur INTEGER;",
        "ALTER TABLE app_themes ADD COLUMN IF NOT EXISTS border_radius INTEGER DEFAULT 24;",
        "ALTER TABLE app_themes ADD COLUMN IF NOT EXISTS border_width INTEGER DEFAULT 1;",
    ]

    try:
        async with pg_manager.get_session() as session:
            for query in queries:
                logger.info(f"Executing: {query}")
                await session.execute(text(query))
            await session.commit()
            logger.info("✅ All structural design columns added successfully.")
    except Exception as e:
        logger.error(f"❌ Error adding columns: {e}")


if __name__ == "__main__":
    asyncio.run(add_theme_columns())
