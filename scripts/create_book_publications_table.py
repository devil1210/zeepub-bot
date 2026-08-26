import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from core.db_manager_pg import pg_manager

STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS book_publications (
        id SERIAL PRIMARY KEY,
        book_id VARCHAR(64) NOT NULL REFERENCES books(id) ON DELETE CASCADE,
        platform VARCHAR(50) NOT NULL DEFAULT 'facebook',
        channel_id INTEGER REFERENCES publication_channels(id) ON DELETE SET NULL,
        post_id VARCHAR(128) NOT NULL,
        post_url VARCHAR(1024),
        caption TEXT,
        published_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_book_publications_book_id ON book_publications(book_id);",
    "CREATE INDEX IF NOT EXISTS idx_book_publications_platform ON book_publications(platform);",
    "CREATE INDEX IF NOT EXISTS idx_book_publications_post_id ON book_publications(post_id);",
    "CREATE INDEX IF NOT EXISTS idx_book_publications_published_at ON book_publications(published_at);"
]

async def run_migration():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        for stmt in STATEMENTS:
            await session.execute(text(stmt))
        await session.commit()
    print("✅ Tabla book_publications e índices creados exitosamente en PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(run_migration())
