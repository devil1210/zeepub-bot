"""
Script de sincronización de UUIDs (UUIDv7) de EPUBs en el VPS con PostgreSQL.
Extrae los identificadores únicos asignados por ZeeTools/Zeedif en dc:identifier
y actualiza la columna 'uuid' en la tabla 'books'.
"""
import asyncio
import logging
import os
import sys

# Agregar path raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select, update
from core.db_manager_pg import pg_manager
from models.library import Book, LibrarySource
from utils.epub_extractor import EpubMetadataExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def sync_vps_uuids():
    logger.info("🚀 Iniciando sincronización de UUIDv7 desde los EPUBs del VPS hacia PostgreSQL...")

    total_scanned = 0
    total_updated = 0
    total_already_synced = 0
    missing_files = 0
    no_uuid_in_epub = 0

    async with pg_manager.get_session() as session:
        # 1. Obtener todos los libros registrados en la base de datos
        stmt = select(Book)
        res = await session.execute(stmt)
        books = res.scalars().all()
        total_books = len(books)
        logger.info(f"📚 Total de libros registrados en BD: {total_books}")

        for book in books:
            total_scanned += 1
            filepath = book.filepath

            if not filepath or not os.path.exists(filepath):
                missing_files += 1
                continue

            try:
                # 2. Extraer metadata técnica y dc:identifier del archivo EPUB
                extractor = EpubMetadataExtractor(filepath)
                meta = extractor.extract()
                epub_uuid = meta.get("uuid") if meta else None

                if not epub_uuid:
                    no_uuid_in_epub += 1
                    continue

                # 3. Si el UUID en el EPUB es diferente o no estaba en la BD, actualizarlo
                if book.uuid != epub_uuid:
                    book.uuid = epub_uuid
                    total_updated += 1
                    if total_updated % 50 == 0:
                        await session.commit()
                        logger.info(f"🔄 Progreso: {total_updated} UUIDs actualizados...")
                else:
                    total_already_synced += 1

            except Exception as e:
                logger.error(f"❌ Error procesando {filepath}: {e}")

        # Guardar cambios finales
        await session.commit()

    logger.info("=" * 60)
    logger.info("✅ Sincronización de UUIDv7 completada!")
    logger.info(f"📊 Total procesados: {total_scanned}")
    logger.info(f"✨ UUIDs actualizados en BD: {total_updated}")
    logger.info(f"✔️ Ya estaban sincronizados: {total_already_synced}")
    logger.info(f"⚠️ Archivos no encontrados en disco: {missing_files}")
    logger.info(f"ℹ️ EPUBs sin UUIDv7 en OPF: {no_uuid_in_epub}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(sync_vps_uuids())
