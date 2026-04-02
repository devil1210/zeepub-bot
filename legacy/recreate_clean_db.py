
import asyncio
import os
import sys
from sqlalchemy import create_engine, text

# Add current dir to path
sys.path.append(os.getcwd())

from config.config_settings import config
from models.base import Base
# Import all models
import models.user_models
import models.library_models
import models.download_models
import models.publication_models

async def nuke_and_recreate():
    print("--- NUKE AND RECREATE DB ---")
    try:
        db_url = config.DATABASE_URL
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("+asyncpg", "")
        
        engine = create_engine(db_url)
        
        # Drop all tables manually to be sure
        with engine.connect() as conn:
            print("Dropping all existing tables...")
            conn.execute(text("DROP TABLE IF EXISTS books CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS series CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS series_metadata CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS user_interactions CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS downloads CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS library_items CASCADE;"))
            conn.commit()
            print("Tables dropped.")
        
        print("Recreating all tables from models...")
        Base.metadata.create_all(engine)
        print("✅ Database schema recreated successfully.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(nuke_and_recreate())
