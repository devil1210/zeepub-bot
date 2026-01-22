import asyncio
import os
import sys
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Add path to find modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.base import Base
from models.user_models import AppTheme  # Import to register in Base.metadata

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        logger.error("No DATABASE_URL found.")
        return

    # Ensure async driver for Postgres
    if "postgresql" in db_url and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    # Validar que no sea SQLite
    if "sqlite" in db_url:
        logger.error("SQLite not supported in this environment. Use PostgreSQL.")
        return

    logger.info(f"Connecting to database (driver): {db_url.split(':')[0]}")

    engine = create_async_engine(db_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            logger.info("Creating tables if not exist (app_themes)...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
