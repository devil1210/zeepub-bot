# Patch DATABASE_URL IMMEDIATELY before any local imports
import os

from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL", "")
if "db:5432" in db_url:
    os.environ["DATABASE_URL"] = db_url.replace("db:5432", "localhost:5432")

import asyncio
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook
from utils.epub_extractor import EpubMetadataExtractor


async def fix_technical_metadata():
    logger.info("🚀 Starting technical metadata extraction for existing books...")

    try:
        async with pg_manager.get_session() as session:
            # 1. Get all books without word count
            result = await session.execute(
                select(LocalBook).where((LocalBook.word_count == 0) | (LocalBook.word_count.is_(None)))
            )
            books = result.scalars().all()

            logger.info(f"🔍 Found {len(books)} books needing update.")

            updated_count = 0
            for i, book in enumerate(books):
                if not book.filepath or not os.path.exists(book.filepath):
                    logger.warning(f"⚠️ File not found: {book.filepath}")
                    continue

                try:
                    logger.info(f"[{i + 1}/{len(books)}] Extracting: {os.path.basename(book.filepath)}")
                    extractor = EpubMetadataExtractor(book.filepath)
                    meta = extractor.extract()

                    if meta:
                        book.word_count = meta.get("word_count", 0)
                        book.page_count = meta.get("page_count", 0)
                        book.reading_time = meta.get("reading_time", 0)
                        book.epub_version = meta.get("version")

                        # Also attempt to get ISBN/ASIN if missing
                        if not book.isbn:
                            book.isbn = meta.get("isbn")
                        if not book.asin:
                            book.asin = meta.get("asin")

                        updated_count += 1

                        # Commit every 10 books to show progress and avoid huge transaction
                        if updated_count % 10 == 0:
                            await session.commit()
                            logger.info(f"✅ Committed {updated_count} updates.")

                except Exception as e:
                    logger.error(f"❌ Error processing {book.filepath}: {e}")

            await session.commit()
            logger.info(f"🏁 Completed. Total updated: {updated_count} books.")

    except Exception as e:
        logger.error(f"❌ Critical error: {e}")


if __name__ == "__main__":
    asyncio.run(fix_technical_metadata())
