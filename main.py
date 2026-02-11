#!/usr/bin/env python3
import asyncio
import logging
import os

from config.config_settings import config
from core.bot import ZeePubBot
from core.optimized_sync_engine import optimized_sync_engine
from services.theme_sync_service import theme_sync_service

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
# Silenciar bibliotecas ruidosas
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# Detectar Infisical
if os.getenv("INFISICAL_PROJECT_ID") or os.getenv("INFISICAL_ENVIRONMENT"):
    logger.info("🔐 Secrets loaded via Infisical Cloud")


async def auto_scan_library():
    """Función de escaneo automático de la biblioteca."""
    try:
        from services.scanner_service import ScannerService

        # No usar os.getenv("LOCAL_LIBRARIES") ya que scanner toma config_json en __init__
        # pero es mejor pasarlo vacío si no lo usamos para este auto_scan
        # Dependiendo del diseño deseado.
        # Si queremos escanear TODAS las fuentes de DB:

        scanner = ScannerService("{}")
        logger.info("Starting automatic library scan (All DB Sources)...")

        results = await scanner.sync_all(force_scan=False)
        if results:
            logger.info(f"Auto scan completed: {results}")
    # Auto scan is now standard, no extra logs here unless needed

    except Exception as e:
        logger.error(f"Error in auto scan library: {e}")


async def fix_schema_if_needed():
    """Fix missing database columns before starting bot"""
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine

        # Use the same DATABASE_URL as the bot
        DATABASE_URL = config.DATABASE_URL
        if not DATABASE_URL:
            logger.error("DATABASE_URL not configured. Skipping schema check.")
            return

        logger.info("Checking database schema (PostgreSQL)...")
        engine = create_async_engine(DATABASE_URL, echo=False)

        async with engine.begin() as conn:
            # --- TABLAS MAESTRAS ---
            # Tabla de metadatos de series
            await conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS series_metadata (
                    id SERIAL PRIMARY KEY,
                    series_name VARCHAR(255) NOT NULL,
                    series_hash VARCHAR(64) UNIQUE NOT NULL,
                    author VARCHAR(255),
                    author_jap VARCHAR(255),
                    illustrator VARCHAR(255),
                    illustrator_jap VARCHAR(255),
                    description TEXT,
                    tags JSONB,
                    cover_url VARCHAR(1024),
                    book_count INTEGER DEFAULT 0,
                    rating_average FLOAT DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                );
            """)
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_series_metadata_hash "
                    "ON series_metadata(series_hash);"
                )
            )

            # Tabla de administradores (Local)
            await conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                );
            """)
            )

            # --- OPTIMIZACIONES DE RENDIMIENTO 2025 ---
            # Índices en historiales
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_upload_history_user_id "
                    "ON upload_history(user_id);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_download_history_user_id "
                    "ON download_history(user_id);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_ratings_user_id ON user_ratings(user_id);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_downloads_user_id "
                    "ON user_downloads(user_id);"
                )
            )

            # Índices en claves foráneas
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_users_level_id ON users(level_id);")
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_levels_default_theme_id "
                    "ON user_levels(default_theme_id);"
                )
            )

            # Relación de series optimizada (Integer) - Debe ir después de crear series_metadata
            await conn.execute(
                text("""
                ALTER TABLE local_books 
                ADD COLUMN IF NOT EXISTS series_metadata_id INTEGER REFERENCES series_metadata(id);
            """)
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_local_books_series_metadata_id "
                    "ON local_books(series_metadata_id);"
                )
            )

            # --- COLUMNAS DE METADATA EXTENDIDA (MIGRACIÓN 2025) ---
            # local_books
            await conn.execute(
                text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS author_jap VARCHAR(255);")
            )
            await conn.execute(
                text(
                    "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS illustrator_jap VARCHAR(255);"
                )
            )
            await conn.execute(
                text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS spanish_title VARCHAR(512);")
            )
            await conn.execute(
                text(
                    "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS is_uncensored "
                    "INTEGER DEFAULT 0;"
                )
            )
            await conn.execute(
                text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);")
            )

            # user_levels
            await conn.execute(
                text(
                    "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS default_theme_id "
                    "INTEGER DEFAULT NULL;"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS allow_theme_templates "
                    "BOOLEAN DEFAULT FALSE;"
                )
            )
            await conn.execute(
                text(
                    "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_upload_epub "
                    "BOOLEAN DEFAULT FALSE;"
                )
            )

            # users
            await conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS can_upload_epub "
                    "BOOLEAN DEFAULT FALSE;"
                )
            )
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;")
            )
            await conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at "
                    "TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());"
                )
            )

            # --- TABLAS DE PUBLICACIÓN (FASE 3) ---
            await conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS publication_channels (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    platform VARCHAR(20) NOT NULL,
                    target_id VARCHAR(100) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    config JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                );
            """)
            )

            await conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS publication_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    platform VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                );
            """)
            )

            await conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS publication_queue (
                    id SERIAL PRIMARY KEY,
                    book_hash VARCHAR(64) NOT NULL,
                    channel_id INTEGER REFERENCES publication_channels(id),
                    template_id INTEGER REFERENCES publication_templates(id),
                    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    published_at TIMESTAMP WITH TIME ZONE,
                    error_message TEXT,
                    payload JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                );
            """)
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_publication_queue_status "
                    "ON publication_queue(status);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_publication_queue_scheduled "
                    "ON publication_queue(scheduled_for);"
                )
            )

        await engine.dispose()

        logger.info("Database schema check completed successfully.")

    except Exception as e:
        logger.warning(f"Schema check failed: {e}")


async def initialize_application():
    """Initialize application components before starting bot."""
    # Fix schema before starting bot
    await fix_schema_if_needed()

    # Initial theme sync from Supabase to local
    logger.info("Starting initial theme synchronization...")
    sync_result = await theme_sync_service.initial_sync()
    if sync_result.get("status") == "success":
        logger.info(
            f"Initial sync completed: {sync_result.get('added', 0)} themes added, "
            f"{sync_result.get('updated', 0)} updated"
        )
    else:
        logger.warning(f"Initial sync failed: {sync_result.get('error', 'Unknown error')}")

    # Schedule daily sync
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler()

    # Schedule daily sync at 3:00 AM
    scheduler.add_job(
        theme_sync_service.daily_sync,
        "cron",
        hour=3,
        minute=0,
        id="daily_theme_sync",
        replace_existing=True,
    )

    # Schedule automatic library scan every 2 hours
    scheduler.add_job(
        lambda: asyncio.create_task(auto_scan_library()),
        "cron",
        hour="*/2",  # Every 2 hours
        minute=0,
        id="auto_library_scan",
        replace_existing=True,
    )

    # Schedule publication queue processing every 5 minutes
    from services.publisher.publisher_service import publisher_service

    scheduler.add_job(
        lambda: asyncio.create_task(publisher_service.process_queue()),
        "interval",
        minutes=5,
        id="publication_queue_processing",
        replace_existing=True,
    )

    scheduler.start()

    logger.info("Daily theme sync scheduled for 3:00 AM")
    logger.info("Automatic library scan scheduled every 2 hours")

    # Start optimized sync engine
    await optimized_sync_engine.start()
    logger.info("Optimized sync engine started")


def main():
    # Setup global logging to capture logs in memory for the admin panel
    from utils.log_manager import setup_global_logging

    setup_global_logging()

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
