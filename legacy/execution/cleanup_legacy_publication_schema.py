import asyncio
import os

# Override DATABASE_URL for local execution (MUST be before core imports)
os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

from sqlalchemy import text
from core.v4_db_manager import db_v4

async def cleanup_schema():
    print("🧹 Cleaning up legacy publication tables to allow V4 UUID schema...")
    
    tables_to_drop = [
        "publication_queue",
        "publication_channels",
        "publication_templates",
        "discovered_chats"
    ]
    
    async with db_v4._engine.begin() as conn:
        for table in tables_to_drop:
            print(f"Dropping table if exists: {table}")
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
    
    print("✅ Cleanup complete. Tables ready for recreation with V4 schema.")

if __name__ == "__main__":
    asyncio.run(cleanup_schema())
    asyncio.run(db_v4.dispose())
