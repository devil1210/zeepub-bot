import asyncio
import logging
import os
import sys

# Añadir el directorio raíz al path para poder importar core y models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from core.schema_orchestrator import schema_orchestrator

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def reparar_esquema():
    """
    Herramienta de reparación de emergencia para el esquema de Zeepub.
    Fuerza la creación de tablas y añade columnas faltantes.
    """
    logger.info("🚀 Iniciando reparación de emergencia del esquema...")

    try:
        # 1. Inicializar conexión
        await pg_manager.initialize()

        # 2. Ejecutar orquestador (esto registrará todos los modelos y creará tablas faltantes)
        await schema_orchestrator.initialize_schema()

        # 3. Verificaciones manuales de columnas conflictivas (Doble Check)
        async with pg_manager.get_session() as session:
            # Lista de reparaciones manuales críticas
            reparaciones = [
                ("series_metadata", "series_spanish", "VARCHAR(512)"),
                ("series_metadata", "series_english", "VARCHAR(512)"),
                ("download_history", "series_hash", "VARCHAR(64)"),
                ("user_downloads", "series_hash", "VARCHAR(64)"),
                ("download_history", "clean_title", "VARCHAR(512)"),
                ("publication_templates", "is_default", "BOOLEAN DEFAULT FALSE"),
                ("publication_templates", "extra_config", "JSONB"),
                ("user_levels", "can_upload_epub", "BOOLEAN DEFAULT FALSE"),
                ("users", "can_upload_epub", "BOOLEAN DEFAULT FALSE"),
            ]

            for table, col, col_type in reparaciones:
                # Verificar existencia de tabla
                table_exists = (
                    await session.execute(
                        text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                    )
                ).scalar()

                if table_exists:
                    # Verificar existencia de columna
                    col_exists = (
                        await session.execute(
                            text(
                                f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{col}')"
                            )
                        )
                    ).scalar()

                    if not col_exists:
                        logger.warning(f"🔧 Arreglando columna faltante: {table}.{col}")
                        await session.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                        logger.info(f"✅ Columna {col} añadida a {table}.")
                    else:
                        logger.debug(f"🗸 Columna {table}.{col} ya existe.")
                else:
                    logger.error(f"❌ La tabla {table} no existe a pesar de los intentos de creación.")

        await session.commit()
        logger.info("✨ Reparación completada correctamente.")

    except Exception as e:
        logger.critical(f"💥 Error fatal durante la reparación: {e}")
        raise
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(reparar_esquema())
