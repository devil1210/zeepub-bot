import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config.config_settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct connection string for Postgres (assuming it's available in env or config)
# If config uses sqlite by default, we force the postgres URL if available
DATABASE_URL = config.DATABASE_URL
if "sqlite" in DATABASE_URL:
    logger.error("Error: DATABASE_URL points to SQLite. Check configuration.")


async def fix_postgres_schema():
    logger.info("Connecting to Postgres to fix schema...")

    # Ensure we use async driver
    target_url = DATABASE_URL
    if target_url.startswith("postgresql://"):
        target_url = target_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Logic for local development (outside docker)
    if "@db:" in target_url:
        logger.info(
            "Detected '@db' host in URL, likely running outside Docker. Falling back to localhost..."
        )
        target_url = target_url.replace("@db:", "@localhost:", 1)

    try:
        engine = create_async_engine(target_url, echo=True)
        async with engine.begin() as conn:
            # Check if column exists
            logger.info("Checking for default_theme_id column in user_levels...")

            # This is a safe idempotent operation in Postgres
            await conn.execute(
                text("""
                ALTER TABLE user_levels 
                ADD COLUMN IF NOT EXISTS default_theme_id INTEGER DEFAULT NULL REFERENCES app_themes(id);
            """)
            )
            logger.info("Added default_theme_id column successfully (if it didn't exist).")

            await conn.execute(
                text("""
                ALTER TABLE user_levels 
                ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;
            """)
            )
            logger.info("Added allow_theme_templates column.")

            # --- NUEVAS MEJORAS DE RENDIMIENTO ---

            # 1. Índices en Tablas de Historial (Punto 3 del plan)
            logger.info("Añadiendo índices a tablas de historial...")
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_upload_history_user_id ON upload_history(user_id);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_download_history_user_id ON download_history(user_id);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_ratings_user_id ON user_ratings(user_id);"
                )
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_downloads_user_id ON user_downloads(user_id);"
                )
            )

            # 2. Claves Foráneas con Índice (Punto 1 del plan anterior)
            logger.info("Añadiendo índices a claves foráneas críticas...")
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_users_level_id ON users(level_id);")
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_user_levels_default_theme_id ON user_levels(default_theme_id);"
                )
            )

            # 3. Optimización de Series (Punto 2 del plan - Integer vs String)
            logger.info("Optimizando relación de series (LocalBook -> SeriesMetadata)...")
            await conn.execute(
                text("""
                ALTER TABLE local_books 
                ADD COLUMN IF NOT EXISTS series_metadata_id INTEGER REFERENCES series_metadata(id);
            """)
            )
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_local_books_series_metadata_id ON local_books(series_metadata_id);"
                )
            )

            # 4. Spanish Title y Book ID (Fix Errors Section)
            logger.info("Añadiendo columnas para corrección de errores de metadatos y descargas...")
            await conn.execute(
                text("""
                ALTER TABLE series_metadata 
                ADD COLUMN IF NOT EXISTS spanish_title VARCHAR(255);
            """)
            )
            await conn.execute(
                text("""
                ALTER TABLE download_history 
                ADD COLUMN IF NOT EXISTS book_id INTEGER REFERENCES local_books(id);
            """)
            )
            logger.info("Columnas spanish_title y book_id añadidas satisfactoriamente.")

        await engine.dispose()
        logger.info("Schema fix completed.")

    except Exception as e:
        logger.error(f"Error fixing schema: {e}")


if __name__ == "__main__":
    asyncio.run(fix_postgres_schema())
