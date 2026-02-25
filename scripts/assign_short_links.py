import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook
from utils.helpers import generate_short_link


async def main():
    print("Checking for books without short_links...")
    await pg_manager.initialize()

    async with pg_manager.get_session() as session:
        # Find books with no short_link
        stmt = select(LocalBook).where(LocalBook.short_link.is_(None))
        result = await session.execute(stmt)
        books = result.scalars().all()

        if not books:
            print("All books already have a short_link. Nothing to do.")
            await pg_manager.close()
            return

        print(f"Found {len(books)} books without a short_link. Generating...")

        updates = 0
        for book in books:
            book.short_link = generate_short_link()
            updates += 1

        await session.commit()
        print(f"Successfully generated and saved short_links for {updates} books.")

    await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
