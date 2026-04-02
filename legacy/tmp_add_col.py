import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def add_columns():
    db_url = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(db_url)
    
    async with engine.begin() as conn:
        print("Checking/Adding columns to series_metadata...")
        await conn.execute(text("ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS series_english VARCHAR(255);"))
        
        print("Checking/Adding columns to archived_series...")
        # Check if table exists first
        res = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'archived_series');"))
        exists = res.scalar()
        if exists:
            await conn.execute(text("ALTER TABLE archived_series ADD COLUMN IF NOT EXISTS series_english VARCHAR(255);"))
            print("Added to archived_series.")
        else:
            print("archived_series table does not exist, skipping.")
            
    await engine.dispose()
    print("Done.")

if __name__ == "__main__":
    asyncio.run(add_columns())
