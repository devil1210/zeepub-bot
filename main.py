#!/usr/bin/env python3
import logging
import asyncio
from config.config_settings import config
from core.bot import ZeePubBot

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
# Silenciar bibliotecas ruidosas
logging.getLogger("aiosqlite").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def fix_schema_if_needed():
    """Fix missing database columns before starting bot"""
    if not config.ENABLE_POSTGRES_PLUGIN:
        return
        
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # Use the same DATABASE_URL as the bot
        DATABASE_URL = config.DATABASE_URL
        if "sqlite" in DATABASE_URL:
            return
            
        logger.info("Checking database schema...")
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        async with engine.begin() as conn:
            # Add default_theme_id column if missing
            await conn.execute(text("""
                ALTER TABLE user_levels 
                ADD COLUMN IF NOT EXISTS default_theme_id INTEGER DEFAULT NULL;
            """))
            
            # Add allow_theme_templates column if missing  
            await conn.execute(text("""
                ALTER TABLE user_levels 
                ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;
            """))
            
        await engine.dispose()
        logger.info("Database schema check completed.")
        
    except Exception as e:
        logger.warning(f"Schema check failed: {e}")


def main():
    logger.info("Iniciando ZeePub Bot...")
    is_valid, missing = config.validate()
    if not is_valid:
        logger.error(f"Faltan variables de entorno: {', '.join(missing)}")
        return

    # Informar sobre la base de datos activa
    if config.DATABASE_URL:
        logger.info("📦 Base de Datos: PostgreSQL (Configurada)")
    else:
        logger.info("📦 Base de Datos: SQLite (Activa por defecto)")

    # Fix schema before starting bot
    asyncio.run(fix_schema_if_needed())

    bot = ZeePubBot()
    bot.start()
    logger.info("Bot detenido.")


if __name__ == "__main__":
    main()
