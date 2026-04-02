
import asyncio
import os
import sys
from sqlalchemy import create_engine

# Add current dir to path
sys.path.append(os.getcwd())

from config.config_settings import config
from models.base import Base
# Import all models to ensure they are registered
import models.user_models
import models.library_models
import models.download_models
import models.publication_models

async def sync_master():
    print("--- MASTER SCHEMA SYNC ---")
    try:
        db_url = config.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("+asyncpg", "")
        
        engine = create_engine(db_url)
        print(f"Syncing models to: {db_url}")
        
        # This will create any missing tables and columns that SQLAlchemy can manage
        Base.metadata.create_all(engine)
        print("✅ Tables assured.")
        
    except Exception as e:
        print(f"❌ error: {e}")

if __name__ == "__main__":
    asyncio.run(sync_master())
