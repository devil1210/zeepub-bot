import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from config.config_settings import config

# Direct connection string for Postgres (assuming it's available in env or config)
# If config uses sqlite by default, we force the postgres URL if available
DATABASE_URL = config.DATABASE_URL
if "sqlite" in DATABASE_URL:
    logger.error("Error: DATABASE_URL points to SQLite. Check configuration.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_postgres_schema():
    if not config.ENABLE_POSTGRES_PLUGIN:
        logger.info("Postgres plugin not enabled. Skipping.")
        return

    logger.info(f"Connecting to Postgres to fix schema: {DATABASE_URL}")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.begin() as conn:
            # Check if column exists
            logger.info("Checking for default_theme_id column in user_levels...")
            
            # This is a safe idempotent operation in Postgres
            await conn.execute(text("""
                ALTER TABLE user_levels 
                ADD COLUMN IF NOT EXISTS default_theme_id INTEGER DEFAULT NULL REFERENCES app_themes(id);
            """))
            logger.info("Added default_theme_id column successfully (if it didn't exist).")

            await conn.execute(text("""
                ALTER TABLE user_levels 
                ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;
            """))
            logger.info("Added allow_theme_templates column successfully (if it didn't exist).")
            
        await engine.dispose()
        logger.info("Schema fix completed.")
        
    except Exception as e:
        logger.error(f"Error fixing schema: {e}")

if __name__ == "__main__":
    asyncio.run(fix_postgres_schema())
