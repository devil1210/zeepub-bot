import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import func, select

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv(override=True)

# Determine DB URL
db_url = os.environ.get("DATABASE_URL", "postgresql://zeepub:zeepub@db:5432/zeepub")
if "@db:" in db_url:
    db_url = db_url.replace("@db:", "@127.0.0.1:")
elif "@localhost:" in db_url:
    db_url = db_url.replace("@localhost:", "@127.0.0.1:")
if db_url.startswith("postgresql://"):
    db_url = "postgresql+asyncpg" + db_url[10:]
os.environ["DATABASE_URL"] = db_url

from core.db_manager_pg import pg_manager
from models.library import LocalBook


async def check_stats():
    await pg_manager.initialize()
    async with pg_manager.get_session() as session:
        # Total books
        stmt_total = select(func.count(LocalBook.id))
        res_total = await session.execute(stmt_total)
        total = res_total.scalar()

        # Linked books
        stmt_linked = select(func.count(LocalBook.id)).where(LocalBook.series_metadata_id.is_not(None))
        res_linked = await session.execute(stmt_linked)
        linked = res_linked.scalar()

        # Books with series_hash but no metadata_id
        stmt_unlinked = (
            select(func.count(LocalBook.id))
            .where(LocalBook.series_metadata_id.is_(None))
            .where(LocalBook.series_hash.is_not(None))
        )
        res_unlinked = await session.execute(stmt_unlinked)
        unlinked = res_unlinked.scalar()

        print(f"Total books: {total}")
        print(f"Linked books: {linked}")
        print(f"Unlinked (but have hash): {unlinked}")

    await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check_stats())
