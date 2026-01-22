"""
Create theme_sync_logs table in PostgreSQL
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config.config_settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_theme_sync_logs_table():
    """Create the theme_sync_logs table if it doesn't exist."""
    
    if not config.ENABLE_POSTGRES_PLUGIN:
        logger.info("PostgreSQL plugin not enabled. Skipping table creation.")
        return
    
    DATABASE_URL = config.DATABASE_URL
    if not DATABASE_URL:
        logger.error("DATABASE_URL not configured")
        return
    
    logger.info(f"Creating theme_sync_logs table in PostgreSQL")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            # Create the table with all necessary columns
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS theme_sync_logs (
                    id SERIAL PRIMARY KEY,
                    sync_type VARCHAR(50) NOT NULL,
                    direction VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    local_themes_before INTEGER DEFAULT 0,
                    local_themes_after INTEGER DEFAULT 0,
                    supabase_themes_before INTEGER DEFAULT 0,
                    supabase_themes_after INTEGER DEFAULT 0,
                    themes_added INTEGER DEFAULT 0,
                    themes_updated INTEGER DEFAULT 0,
                    themes_deleted INTEGER DEFAULT 0,
                    errors TEXT,
                    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    completed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Create indexes for better performance
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_theme_sync_logs_status ON theme_sync_logs(status);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_theme_sync_logs_started_at ON theme_sync_logs(started_at);
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_theme_sync_logs_sync_type ON theme_sync_logs(sync_type);
            """))
            
        await engine.dispose()
        logger.info("theme_sync_logs table created successfully")
        
    except Exception as e:
        logger.error(f"Error creating theme_sync_logs table: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_theme_sync_logs_table())
