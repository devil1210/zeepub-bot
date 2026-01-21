import sys
import os

# Ensure local modules can be imported
sys.path.append(os.getcwd())

import asyncio
import sqlite3
from sqlalchemy import text
from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_db")

DB_PATH = config.URL_CACHE_DB_PATH

async def migrate_sqlite():
    logger.info(f"Checking SQLite at {DB_PATH}")
    if not os.path.exists(DB_PATH):
        logger.warning("SQLite database file not found. Skipping.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "photo_url" not in columns:
        logger.info("Adding photo_url to users table (SQLite)")
        cursor.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
    
    # Check user_levels table
    cursor.execute("PRAGMA table_info(user_levels)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "allow_theme_templates" not in columns:
        logger.info("Adding allow_theme_templates to user_levels table (SQLite)")
        cursor.execute("ALTER TABLE user_levels ADD COLUMN allow_theme_templates BOOLEAN DEFAULT 0")

    if "ui_glow_intensity" not in columns:
        logger.info("Adding ui_glow_intensity to user_levels table (SQLite)")
        cursor.execute("ALTER TABLE user_levels ADD COLUMN ui_glow_intensity FLOAT DEFAULT 0.5")

    conn.commit()
    conn.close()
    logger.info("SQLite migration done.")

async def migrate_postgres():
    if not config.ENABLE_POSTGRES_PLUGIN:
        logger.info("Postgres plugin not enabled. Skipping.")
        return

    logger.info("Checking Postgres/Supabase via pg_manager")
    try:
        async with pg_manager.get_session() as session:
            # Add photo_url to users
            try:
                await session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url TEXT"))
                logger.info("Checked photo_url in users (Postgres)")
            except Exception as e:
                logger.error(f"Error adding photo_url to Postgres: {e}")

            # Add allow_theme_templates to user_levels
            try:
                await session.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE"))
                logger.info("Checked allow_theme_templates in user_levels (Postgres)")
            except Exception as e:
                logger.error(f"Error adding allow_theme_templates to Postgres: {e}")

            # Add ui_glow_intensity to user_levels
            try:
                await session.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_glow_intensity FLOAT DEFAULT 0.5"))
                logger.info("Checked ui_glow_intensity in user_levels (Postgres)")
            except Exception as e:
                logger.error(f"Error adding ui_glow_intensity to Postgres: {e}")

            await session.commit()
        logger.info("Postgres/Supabase migrations done.")
    except Exception as e:
        logger.error(f"Failed to connect to Postgres for migration: {e}")

async def main():
    await migrate_sqlite()
    await migrate_postgres()

if __name__ == "__main__":
    asyncio.run(main())
