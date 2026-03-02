import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DATABASE_URL to use localhost tunnel
os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

# Re-create engine with new URL
from config.config_settings import config

config.DATABASE_URL = os.environ["DATABASE_URL"]
import utils.library_db

utils.library_db.engine = utils.library_db.create_library_engine()  # Force re-init with new URL
import logging

from utils.library_db import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")


async def cleanup_library():
    """
    Verifica la existencia física de CADA libro en la base de datos local.
    Si no existe, lo elimina/archiva.
    """
    logger.info(f"Starting Library Integrity Check on {config.DATABASE_URL}...")

    from services.scanner_service import ScannerService

    with get_session() as session:
        stats = await ScannerService.cleanup_library_orphans(session, user_id=0)  # 0 for System/Script
        logger.info(f"Integrity check complete: {stats}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(cleanup_library())
