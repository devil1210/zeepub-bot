import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    logger.info("Iniciando migración de permisos de usuario...")

    # Forzamos localhost dado que estamos en un entorno con puertos redireccionados
    db_url = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        try:
            # 1. Agregar allow_theme_templates
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;"
                    )
                )
                logger.info("Columna 'allow_theme_templates' agregada o ya existía.")
            except Exception as e:
                logger.warning(f"Aviso al agregar allow_theme_templates: {e}")

            # 2. Agregar roles
            try:
                await conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN IF NOT EXISTS roles JSONB DEFAULT '[]'::jsonb;"
                    )
                )
                logger.info("Columna 'roles' agregada o ya existía.")
            except Exception as e:
                logger.warning(f"Aviso al agregar roles: {e}")

            logger.info("Migración completada exitosamente.")

        except Exception as e:
            logger.error(f"Error fatal durante la migración: {e}")


if __name__ == "__main__":
    asyncio.run(run_migration())
