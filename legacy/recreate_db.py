
import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from models.base import Base

# Import all models to register them
import models.user_models
import models.library_models
import models.download_models
import models.publication_models

async def recreate_db():
    print("--- RECREATING POSTGRES SCHEMA ---")
    try:
        # Get sync engine from PostgresManager (it might be async, but lets check)
        from sqlalchemy import create_engine
        from config.config_settings import config
        
        db_url = config.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("+asyncpg", "")
        
        sync_engine = create_engine(db_url)
        print(f"Connecting to: {db_url}")
        
        # Drop if needed? No, let's just create_all
        Base.metadata.create_all(sync_engine)
        print("✅ Schema recreated successfully.")
        
    except Exception as e:
        print(f"❌ Error recreating schema: {e}")

if __name__ == "__main__":
    asyncio.run(recreate_db())
