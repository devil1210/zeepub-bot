#!/usr/bin/env python3
"""
Re-escaneo completo de la librería para recalcular metadatos con el fix de signos de interrogación
Ejecutar en VPS: docker exec zeepub-api python migrations/rescan_complete_library.py
"""

import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from services.scanner_service import ScannerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def rescan_complete_library():
    """Re-escanea toda la librería para recalcular metadatos"""

    logger.info("🔄 Iniciando re-escaneo completo de la librería...")

    # 1. Limpiar tablas temporales si existen
    async with pg_manager.get_session() as session:
        logger.info("🧹 Limpiando datos temporales...")

        # Limpiar datos de escaneo previos
        cleanup_queries = [
            "DELETE FROM upload_books WHERE processed = false",
            "DELETE FROM metadata_proposals WHERE status = 'pending'",
            "UPDATE series_metadata SET book_count = 0 WHERE book_count IS NULL",
        ]

        for query in cleanup_queries:
            await session.execute(text(query))

        await session.commit()
        logger.info("✅ Limpieza completada")

    # 2. Obtener configuración de librerías
    import os

    libs_json = os.getenv("LOCAL_LIBRARIES")
    if not libs_json:
        logger.error("❌ LOCAL_LIBRARIES no configurado")
        return

    logger.info(f"📚 Librerías configuradas: {libs_json}")

    # 3. Iniciar escaneo completo
    try:
        scanner = ScannerService(libs_json)

        # Escaneo forzado (ignora caché)
        logger.info("🔍 Iniciando escaneo forzado de todos los archivos...")
        await scanner.sync_all(force_scan=True, soft_scan=False)

        logger.info("✅ Re-escaneo completado exitosamente")
        logger.info("📊 Los metadatos han sido recalculados con el fix de signos de interrogación")

    except Exception as e:
        logger.error(f"❌ Error durante re-escaneo: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(rescan_complete_library())
