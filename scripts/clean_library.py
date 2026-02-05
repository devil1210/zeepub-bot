import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DATABASE_URL to use localhost tunnel
os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

import asyncio
from models.library_models import LocalBook, SeriesMetadata, ArchivedBook, ArchivedSeries
# Re-create engine with new URL
from config.config_settings import config
config.DATABASE_URL = os.environ["DATABASE_URL"]
import utils.library_db
utils.library_db.engine = utils.library_db.create_library_engine() # Force re-init with new URL
from utils.library_db import get_session

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")

def cleanup_library():
    """
    Verifica la existencia física de CADA libro en la base de datos local.
    Si no existe, lo elimina/archiva.
    Si una serie se queda sin libros, la elimina/archiva.
    """
    logger.info(f"Starting Library Integrity Check on {config.DATABASE_URL}...")
    
    deleted_books = 0
    deleted_series = 0
    
    with get_session() as session:
        # 1. Fetch all books (filepath, id, series_hash)
        books = session.query(LocalBook).all()
        logger.info(f"Checking {len(books)} books for physical existence...")

        affected_hashes = set()

        for book in books:
            # WARNING: This checks on LOCALHOST aka the machine running the script.
            # If running on Dev Machine checking Remote files, this WILL DELETE EVERYTHING if paths don't match.
            # But the user asked "verificar rapidamente", implying they are on the server or paths are mapped.
            # Assuming Mapped Drive or SSH execution. 
            # In this context, user paths are C:\Users\charl\OneDrive... 
            # If DB paths are /library/..., os.path.exists will fail on Windows.
            
            # Smart check: if valid Windows path not exists -> delete
            # If linux path -> warn and skip unless confirmed
            
            if not os.path.exists(book.filepath):
                # Extra safety: Check if it's a linux path running on windows
                if book.filepath.startswith("/") and sys.platform == "win32":
                    # Try to map it? Or just skip?
                    # User asked to verify. If I can't verify, I shouldn't delete blindly.
                    # But user said "verificar la existencia", implying they want this check.
                    # Let's assume the user knows the paths might mismatch if context is wrong.
                    # WAIT. The user has "C:/Users/charl/OneDrive/Zeepubs..." mapped in .env LOCAL_LIBRARIES?
                    # Not necessarily used here.
                    
                    # Safer approach: Log missing, don't delete if platform mismatch seems likely
                     logger.warning(f"MISSING (Platform mismatch?): {book.filepath}")
                     continue

                logger.warning(f"MISSING (Deleting): {book.filepath}")
                
                # Archive
                archived = ArchivedBook(
                    series_hash=book.series_hash,
                    book_hash=book.book_hash,
                    title=book.title,
                    filename=book.filename,
                    last_filepath=book.filepath,
                    volume=book.volume,
                    author=book.author,
                    book_type=book.book_type,
                    original_book_id=book.id,
                    reason="integrity_check_missing"
                )
                session.add(archived)
                
                if book.series_hash:
                    affected_hashes.add(book.series_hash)
                
                session.delete(book)
                deleted_books += 1
        
        session.commit()
        logger.info(f"Removed {deleted_books} missing books.")

        # 2. Check affected series
        if affected_hashes:
            logger.info(f"Checking {len(affected_hashes)} potentially empty series...")
            for s_hash in affected_hashes:
                count = session.query(LocalBook).filter_by(series_hash=s_hash).count()
                if count == 0:
                    series = session.query(SeriesMetadata).filter_by(series_hash=s_hash).first()
                    if series:
                        logger.info(f"Removing empty series: {series.series_name}")
                        archived_s = ArchivedSeries(
                            series_name=series.series_name,
                            series_spanish=series.series_spanish,
                            series_hash=series.series_hash,
                            author=series.author,
                            description=series.description,
                            tags=series.tags,
                            cover_url=series.cover_url,
                            book_type=series.book_type,
                            publisher=series.publisher,
                            original_series_id=series.id
                        )
                        session.add(archived_s)
                        session.delete(series)
                        deleted_series += 1
            
            session.commit()
            logger.info(f"Removed {deleted_series} empty series.")
        
        # 3. Force Recalculate Counts for ALL series (just in case)
        logger.info("Recalculating book counts for all series...")
        all_series = session.query(SeriesMetadata).all()
        for s in all_series:
            real_count = session.query(LocalBook).filter_by(series_hash=s.series_hash).count()
            if s.book_count != real_count:
                logger.info(f"Fixing count for {s.series_name}: {s.book_count} -> {real_count}")
                s.book_count = real_count
        
        session.commit()
        logger.info("Integrity check complete.")

if __name__ == "__main__":
    cleanup_library()
