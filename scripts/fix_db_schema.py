
import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Getting DB URL from env or default
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://zeepub:zeepub@db:5432/zeepub")

# Ensure asyncpg driver
if "postgresql://" in DATABASE_URL and "postgresql+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def migrate():
    print("Connecting to database...")
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            print("Checking and patching schemas...")
            
            # 1. Patch user_ratings
            print("Patching user_ratings...")
            await conn.execute(text("""
                ALTER TABLE user_ratings 
                ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_ratings_book_hash 
                ON user_ratings(book_hash);
            """))
            
            # 2. Patch user_downloads
            print("Patching user_downloads...")
            await conn.execute(text("""
                ALTER TABLE user_downloads 
                ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);
            """))
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_downloads_book_hash 
                ON user_downloads(book_hash);
            """))
            
            # 3. Reload cache (for Supabase/PostgREST)
            print("Reloading schema cache...")
            await conn.execute(text("NOTIFY pgrst, 'reload schema';"))
            
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
