import asyncio
import logging
import os
from datetime import datetime, timedelta
from utils.library_db import DB_PATH
from services.library_backup_service import LibraryBackupService

logger = logging.getLogger(__name__)


async def run_library_backup():
    """Ejecuta el backup de la biblioteca local."""
    try:
        logger.info("Iniciando backup automático de la biblioteca local...")
        # Inicializar servicio (usamos la ruta por defecto)
        backup_service = LibraryBackupService(db_path=DB_PATH)
        backup_path = backup_service.create_backup(compress=True)
        logger.info(f"Backup automático completado: {backup_path}")
    except Exception as e:
        logger.error(f"Error en backup automático de la biblioteca: {e}", exc_info=True)


async def library_backup_scheduler():
    """Tarea que ejecuta el backup de la biblioteca cada 24 horas."""
    logger.info("Library backup scheduler started")

    # Primera ejecución: 1 minuto después del arranque para no saturar el inicio
    await asyncio.sleep(60)
    await run_library_backup()

    while True:
        try:
            # Esperar 24 horas para el próximo backup
            await asyncio.sleep(86400)
            await run_library_backup()
        except Exception as e:
            logger.error(f"Error en library_backup_scheduler loop: {e}", exc_info=True)
            await asyncio.sleep(3600)  # Reintentar en 1 hora si falla


def start_library_backup_scheduler():
    """Inicia la tarea de backup de la biblioteca en background."""
    asyncio.create_task(library_backup_scheduler())
    logger.info("Library backup scheduler task set to background")
