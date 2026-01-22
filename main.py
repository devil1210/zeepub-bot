#!/usr/bin/env python3
import logging
import asyncio
from config.config_settings import config
from core.bot import ZeePubBot
from services.theme_sync_service import theme_sync_service
from core.optimized_sync_engine import optimized_sync_engine

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
# Silenciar bibliotecas ruidosas
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


async def auto_scan_library():
    """Función de escaneo automático de la biblioteca."""
    try:
        from services.scanner_service import ScannerService
        import os
        
        libs_json = os.getenv("LOCAL_LIBRARIES")
        if not libs_json:
            logger.warning("LOCAL_LIBRARIES not configured for auto scan")
            return
        
        scanner = ScannerService(libs_json)
        logger.info("Starting automatic library scan...")
        
        results = scanner.sync_all(force_scan=False)
        if results:
            logger.info(f"Auto scan completed: {results}")
# Auto scan is now standard, no extra logs here unless needed
            
    except Exception as e:
        logger.error(f"Error in auto scan library: {e}")


async def fix_schema_if_needed():
    """Fix missing database columns before starting bot"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        # Use the same DATABASE_URL as the bot
        DATABASE_URL = config.DATABASE_URL
        if not DATABASE_URL:
            logger.error("DATABASE_URL not configured. Skipping schema check.")
            return
            
        logger.info("Checking database schema (PostgreSQL)...")
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


async def initialize_application():
    """Initialize application components before starting bot."""
    # Fix schema before starting bot
    await fix_schema_if_needed()
    
    # Initial theme sync from Supabase to local
    logger.info("Starting initial theme synchronization...")
    sync_result = await theme_sync_service.initial_sync()
    if sync_result.get('status') == 'success':
        logger.info(f"Initial sync completed: {sync_result.get('added', 0)} themes added, {sync_result.get('updated', 0)} updated")
    else:
        logger.warning(f"Initial sync failed: {sync_result.get('error', 'Unknown error')}")
    
    # Schedule daily sync
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    
    # Schedule daily sync at 3:00 AM
    scheduler.add_job(
        theme_sync_service.daily_sync,
        'cron',
        hour=3,
        minute=0,
        id='daily_theme_sync',
        replace_existing=True
    )
    
    # Schedule automatic library scan every 2 hours
    scheduler.add_job(
        lambda: asyncio.create_task(auto_scan_library()),
        'cron',
        hour='*/2',  # Every 2 hours
        minute=0,
        id='auto_library_scan',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Daily theme sync scheduled for 3:00 AM")
    logger.info("Automatic library scan scheduled every 2 hours")
    
    # Start optimized sync engine
    await optimized_sync_engine.start()
    logger.info("Optimized sync engine started")


def main():
    logger.info("Iniciando ZeePub Bot...")
    is_valid, missing = config.validate()
    if not is_valid:
        logger.error(f"Faltan variables de entorno: {', '.join(missing)}")
        return

    # Informar sobre la base de datos activa
    if config.DATABASE_URL:
        logger.info(" Base de Datos: PostgreSQL (Activa - Mandatorio)")
    else:
        logger.error(" ERROR: DATABASE_URL no configurada. Postgres es requerido.")
        # Opcionalmente salir si es mandatorio
        # return

    # Initialize application
    asyncio.run(initialize_application())

    bot = ZeePubBot()
    bot.start()
    logger.info("Bot detenido.")


if __name__ == "__main__":
    main()
