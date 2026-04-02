
import asyncio
import os
import sys
from sqlalchemy import select, func

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(override=True)

db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/zeepub")
if "@db:" in db_url:
    db_url = db_url.replace("@db:", "@127.0.0.1:")
elif "@localhost:" in db_url:
    db_url = db_url.replace("@localhost:", "@127.0.0.1:")

if db_url.startswith("postgresql://"):
    db_url = "postgresql+asyncpg" + db_url[10:]
elif db_url.startswith("postgres://"):
    db_url = "postgresql+asyncpg" + db_url[8:]

os.environ["DATABASE_URL"] = db_url

from core.db_manager_pg import pg_manager
from models.library import LocalBook, SeriesMetadata

async def debug_death_note():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        print("--- Series Metadata ---")
        stmt_s = select(SeriesMetadata).where(SeriesMetadata.series_name.ilike('%Death Note: Another Note%'))
        res_s = await session.execute(stmt_s)
        series = res_s.scalars().all()
        for s in series:
            print(f"ID: {s.id}, Name: {s.series_name}, Hash: {s.series_hash}, Cover: {s.cover_url}")
            
        print("\n--- Local Books ---")
        stmt_b = select(LocalBook).where(LocalBook.title.ilike('%Death Note: Another Note%'))
        res_b = await session.execute(stmt_b)
        books = res_b.scalars().all()
        for b in books:
            print(f"ID: {b.id}, Title: {b.title}, Hash: {b.book_hash}, SeriesHash: {b.series_hash}, MetadataID: {b.series_metadata_id}")

asyncio.run(debug_death_note())
