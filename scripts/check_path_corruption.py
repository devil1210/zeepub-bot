import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv

# Import ALL models
try:
    import models.agent_models  # noqa: F401
    import models.library_models  # noqa: F401
    import models.publication_models  # noqa: F401
    import models.user_models  # noqa: F401
except ImportError:
    pass

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook

load_dotenv()


async def check_book_details():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    book_id = 1716

    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            stmt = select(LocalBook).where(LocalBook.id == book_id)
            result = await session.execute(stmt)
            book = result.scalar_one_or_none()

            if book:
                print(f"--- BOOK {book_id} DETAILS ---")
                print(f"Title: {repr(book.title)}")
                print(f"Filepath: {repr(book.filepath)}")
                print(f"Filename: {repr(book.filename)}")
                print(f"Series Hash: {book.series_hash}")
                print(f"Short Link: {book.short_link}")

                # Check for other books in same series to see if they have weird paths
                stmt_v = select(LocalBook).where(LocalBook.series_hash == book.series_hash)
                res_v = await session.execute(stmt_v)
                volumenes = res_v.scalars().all()
                print(f"\nVolúmenes de la misma serie ({len(volumenes)}):")
                for v in volumenes:
                    print(f" - ID {v.id}: {repr(v.filename)}")
                    print(f"   Path: {repr(v.filepath)}")
            else:
                print(f"❌ Libro con ID {book_id} no encontrado en la DB local.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check_book_details())
