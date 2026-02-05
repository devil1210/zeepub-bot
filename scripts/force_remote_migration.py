import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Override DATABASE_URL to use localhost tunnel
os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

import logging

# Re-create engine with new URL because utils.library_db initialized it at import time with the old env var
from config.config_settings import config
from utils.library_db import check_migrations

config.DATABASE_URL = os.environ["DATABASE_URL"]

# We need to hack the engine in utils.library_db
import utils.library_db

utils.library_db.engine = utils.library_db.create_library_engine()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Forcing migration on: {config.DATABASE_URL}")
    try:
        check_migrations()
        logger.info("Migration completed successfully via tunnel.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
