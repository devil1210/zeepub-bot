import asyncio
import logging
import os
import sys

# Añadir el path raíz al sistema para importar módulos del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook
from utils.helpers import generate_book_hash, generate_series_hash
from utils.library_db import get_session, init_library_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_hashes_v2")


async def migrate_local_books():
    logger.info("Migrando LocalBook hashes (v2) en Postgres...")
    session = get_session()
    # Procesamos TODOS para asegurar que el hash incluye el traductor ahora
    books = session.query(LocalBook).all()
    logger.info(f"Procesando {len(books)} libros.")

    for book in books:
        # book.series fue eliminado del modelo; la serie vive en series_metadata
        # Para regenerar hashes usamos series_hash que ya está guardado
        series_name = book.series_info.series_name if book.series_info else None

        # Refined Book Hash - NO usar title según nueva especificación
        bh = generate_book_hash(
            series=series_name,
            author=book.author,
            book_type=book.book_type,
            volume=book.volume,
            translator=book.translator,
            layout_by=book.layout_by,
            language=book.language,
            is_uncensored=book.is_uncensored or 0,
            color_mode=book.color_mode or "bw",
        )
        book.book_hash = bh

        # New Series Hash
        sh = generate_series_hash(
            series=series_name,
            author=book.author,
            book_type=book.book_type,
        )
        book.series_hash = sh

        logger.debug(f"Poblando hashes para: {book.title} -> Book:{bh[:8]}, Series:{sh[:8]}")

    session.commit()
    session.close()
    logger.info("LocalBook hashes migrados.")


async def migrate_download_history():
    logger.info("Migrando DownloadHistory hashes (v2) en Postgres...")
    async with pg_manager.get_session() as session:
        result = await session.execute(
            text("SELECT id, title, author, series, volume, clean_title, translator FROM download_history")
        )
        rows = result.fetchall()
        logger.info(f"Procesando {len(rows)} registros de descarga.")

        for row in rows:
            rid, title, author, series, volume, clean_title, translator = row
            # Refined Book Hash for history - Excluyendo título
            bh = generate_book_hash(
                series=series or clean_title,
                author=author,
                volume=volume,
                translator=translator,
                language="es",
            )
            await session.execute(
                text("UPDATE download_history SET book_hash = :hash WHERE id = :id"),
                {"hash": bh, "id": rid},
            )

        await session.commit()
    logger.info("DownloadHistory hashes migrados.")


async def main():
    # 1. Asegurar esquema actualizado
    init_library_db()
    await pg_manager.initialize()

    # 2. Migrar
    await migrate_local_books()
    await migrate_download_history()
    logger.info("Migración v2 completa.")


if __name__ == "__main__":
    asyncio.run(main())
