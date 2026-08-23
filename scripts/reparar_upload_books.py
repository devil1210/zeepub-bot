import asyncio
import logging
from sqlalchemy import text
from utils.postgres_manager import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("schema_fix")

async def fix_upload_books_schema():
    await pg_manager.init_db()
    async with pg_manager.get_session() as session:
        # 1. Obtener columnas actuales
        result = await session.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'upload_books';")
        )
        existing_cols = {row[0] for row in result.fetchall()}
        logger.info(f"Columnas existentes en upload_books: {existing_cols}")

        if not existing_cols:
            logger.info("La tabla upload_books no existe. Se creará con el esquema completo.")
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS upload_books (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT REFERENCES users(telegram_id),
                    original_filename VARCHAR(512) NOT NULL,
                    temp_filepath VARCHAR(1024) NOT NULL,
                    title VARCHAR(512) NOT NULL,
                    series VARCHAR(255),
                    volume FLOAT,
                    author VARCHAR(255),
                    author_jap VARCHAR(255),
                    illustrator VARCHAR(255),
                    illustrator_jap VARCHAR(255),
                    book_type VARCHAR(100),
                    translator VARCHAR(255),
                    layout_by VARCHAR(255),
                    language VARCHAR(10) DEFAULT 'es',
                    is_uncensored INTEGER DEFAULT 0,
                    color_mode VARCHAR(50) DEFAULT 'bw',
                    book_hash VARCHAR(64) NOT NULL,
                    series_hash VARCHAR(64),
                    identity_match VARCHAR(10) DEFAULT 'False',
                    path_collision VARCHAR(10) DEFAULT 'False',
                    processed VARCHAR(10) DEFAULT 'False',
                    upload_metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            await session.commit()
            logger.info("Tabla upload_books creada exitosamente.")
            return

        # 2. Si tiene user_id y no telegram_id, renombrar
        if "user_id" in existing_cols and "telegram_id" not in existing_cols:
            logger.info("Renombrando user_id -> telegram_id en upload_books...")
            await session.execute(text("ALTER TABLE upload_books RENAME COLUMN user_id TO telegram_id;"))
            existing_cols.remove("user_id")
            existing_cols.add("telegram_id")

        # 3. Añadir columnas faltantes
        columns_to_add = [
            ("telegram_id", "BIGINT REFERENCES users(telegram_id)"),
            ("series", "VARCHAR(255)"),
            ("volume", "FLOAT"),
            ("author", "VARCHAR(255)"),
            ("author_jap", "VARCHAR(255)"),
            ("illustrator", "VARCHAR(255)"),
            ("illustrator_jap", "VARCHAR(255)"),
            ("book_type", "VARCHAR(100)"),
            ("translator", "VARCHAR(255)"),
            ("layout_by", "VARCHAR(255)"),
            ("language", "VARCHAR(10) DEFAULT 'es'"),
            ("is_uncensored", "INTEGER DEFAULT 0"),
            ("color_mode", "VARCHAR(50) DEFAULT 'bw'"),
            ("series_hash", "VARCHAR(64)"),
            ("identity_match", "VARCHAR(10) DEFAULT 'False'"),
            ("path_collision", "VARCHAR(10) DEFAULT 'False'"),
            ("processed", "VARCHAR(10) DEFAULT 'False'"),
            ("upload_metadata", "JSONB"),
        ]

        for col_name, col_def in columns_to_add:
            if col_name not in existing_cols:
                logger.info(f"Añadiendo columna faltante: {col_name} {col_def}")
                await session.execute(text(f"ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS {col_name} {col_def};"))

        await session.commit()
        logger.info("✅ Esquema de upload_books actualizado y sincronizado exitosamente.")

if __name__ == "__main__":
    asyncio.run(fix_upload_books_schema())
