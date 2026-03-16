import asyncio
import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(override=True)

db_url = os.environ.get("DATABASE_URL", "postgresql://zeepub:zeepub@db:5432/zeepub")
if "@db:" in db_url:
    db_url = db_url.replace("@db:", "@127.0.0.1:")
elif "@localhost:" in db_url:
    db_url = db_url.replace("@localhost:", "@127.0.0.1:")
if db_url.startswith("postgresql://"):
    db_url = "postgresql+asyncpg" + db_url[10:]
os.environ["DATABASE_URL"] = db_url

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata


async def debug_linkage():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # Check LocalBook
        stmt = select(LocalBook).limit(5)
        res = await session.execute(stmt)
        books = res.scalars().all()

        print(f"--- Libros ({len(books)}) ---")
        for b in books:
            print(f"ID: {b.id}, Series: {b.series}, Hash: {b.series_hash}, SeriesID: {b.series_id}")

        # Check SeriesMetadata
        stmt2 = select(SeriesMetadata).limit(5)
        res2 = await session.execute(stmt2)
        series = res2.scalars().all()

        print(f"\n--- Series Metadata ({len(series)}) ---")
        for s in series:
            print(f"ID: {s.id}, Name: {s.series_name}, Hash: {s.series_hash}")

    await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(debug_linkage())
