
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def fix_metrics_table():
    await pg_manager.initialize()
    async with pg_manager.engine.begin() as conn:
        print("Ensuring user_downloads table exists...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_downloads (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                book_hash VARCHAR(64),
                series_hash VARCHAR(64),
                title VARCHAR(512),
                downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Also ensure indices
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_downloads_user_id ON user_downloads(user_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_downloads_book_hash ON user_downloads(book_hash)"))
        print("Success.")

if __name__ == "__main__":
    asyncio.run(fix_metrics_table())
