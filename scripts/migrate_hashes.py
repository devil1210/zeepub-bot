import asyncio
import logging
import sys
import os

# Añadir el path raíz al sistema para importar módulos del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.library_db import get_session, init_library_db
from models.library_models import LocalBook
from models.download_models import DownloadHistory
from utils.helpers import generate_book_hash, generate_series_hash
from core.db_manager import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_hashes_v2")

async def migrate_local_books():
    logger.info("Migrando LocalBook hashes (v2)...")
    session = get_session()
    # Procesamos TODOS para asegurar que el hash incluye el traductor ahora
    books = session.query(LocalBook).all()
    logger.info(f"Procesando {len(books)} libros.")
    
    for book in books:
        # Refined Book Hash
        bh = generate_book_hash(
            title=book.title,
            author=book.author,
            series=book.series_clean,
            volume=book.volume,
            book_type=book.book_type,
            language=book.language,
            translator=book.translator or book.publisher or book.layout_by
        )
        book.content_hash = bh
        
        # New Series Hash
        sh = generate_series_hash(
            series=book.series_clean or book.series or book.title,
            author=book.author,
            book_type=book.book_type
        )
        book.series_hash = sh
        
        logger.debug(f"Poblando hashes para: {book.title} -> Book:{bh[:8]}, Series:{sh[:8]}")
    
    session.commit()
    session.close()
    logger.info("LocalBook hashes migrados.")

async def migrate_download_history():
    logger.info("Migrando DownloadHistory hashes (v2)...")
    async with db_manager.connection() as conn:
        cursor = await conn.execute("SELECT id, title, author, series, volume, clean_title, translator FROM download_history")
        rows = await cursor.fetchall()
        logger.info(f"Procesando {len(rows)} registros de descarga.")
        
        for row in rows:
            rid, title, author, series, volume, clean_title, translator = row
            # Refined Book Hash for history
            bh = generate_book_hash(
                title=title,
                author=author,
                series=series or clean_title,
                volume=volume,
                language="es",
                translator=translator
            )
            await conn.execute("UPDATE download_history SET book_hash = ? WHERE id = ?", (bh, rid))
        
        await conn.commit()
    logger.info("DownloadHistory hashes migrados.")

async def main():
    # 1. Asegurar esquema actualizado
    init_library_db()
    if hasattr(db_manager, "initialize"):
        await db_manager.initialize()
    
    # 2. Migrar
    await migrate_local_books()
    await migrate_download_history()
    logger.info("Migración v2 completa.")

if __name__ == "__main__":
    asyncio.run(main())
