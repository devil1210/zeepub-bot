import os
import sys
import logging
import hashlib

# Add current directory to path
sys.path.append(os.getcwd())

from utils.library_db import get_session, engine
from models.library_models import LocalBook
from utils.helpers import generate_book_hash, generate_series_hash
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HashMigration")

def migrate():
    session = get_session()
    try:
        books = session.query(LocalBook).all()
        logger.info(f"Iniciando migración de hashes para {len(books)} libros...")
        
        updated_count = 0
        for book in books:
            old_hash = book.book_hash
            
            # Recalcular usando la nueva lógica (series + author + type + vol + trans + layout)
            new_book_hash = generate_book_hash(
                series=book.series,
                author=book.author,
                book_type=book.book_type,
                volume=book.volume,
                translator=book.translator,
                layout_by=book.layout_by,
                language=book.language
            )
            
            new_series_hash = generate_series_hash(
                series=book.series,
                author=book.author,
                book_type=book.book_type
            )
            
            if old_hash != new_book_hash:
                book.book_hash = new_book_hash
                book.series_hash = new_series_hash
                updated_count += 1
                if updated_count % 50 == 0:
                    logger.info(f"Actualizados {updated_count} libros...")
        
        session.commit()
        logger.info(f"Migración completada. Se actualizaron los hashes de {updated_count} libros.")
        
    except Exception as e:
        logger.error(f"Error durante la migración: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
