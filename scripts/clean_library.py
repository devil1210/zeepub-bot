import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DATABASE_URL to use localhost tunnel if needed (usually from env)
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

from core.db_manager_pg import pg_manager
from services.scanner_service import ScannerService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")


async def cleanup_library():
    """
    Verifica la existencia física de CADA libro en la base de datos local.
    Si no existe, lo elimina/archiva.
    """
    logger.info("Starting Library Integrity Check...")

    async with pg_manager.get_session() as session:
        stats = await ScannerService.cleanup_library_orphans(session, user_id=0)  # 0 for System/Script
        logger.info(f"Integrity check complete: {stats}")


if __name__ == "__main__":
    asyncio.run(cleanup_library())
