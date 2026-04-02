
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def migrate():
    await pg_manager.initialize()
    async with pg_manager.engine.begin() as conn:
        print("Creating table discovered_chats if not exists...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS discovered_chats (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(100) UNIQUE NOT NULL,
                title VARCHAR(255) NOT NULL,
                type VARCHAR(50),
                member_count INTEGER DEFAULT 0,
                username VARCHAR(100),
                last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        print("Verifying is_favorite in publication_channels...")
        try:
            await conn.execute(text("ALTER TABLE publication_channels ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE"))
        except Exception as e:
            print(f"Notice: {e}")
        
        print("Migration done.")

if __name__ == "__main__":
    asyncio.run(migrate())
