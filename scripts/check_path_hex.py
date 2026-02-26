import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv
from sqlalchemy import text

from core.db_manager_pg import pg_manager

load_dotenv()


async def check_path_hex():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    book_id = 1716
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            res = await session.execute(text(f"SELECT filepath, book_hash FROM local_books WHERE id={book_id}"))
            row = res.one()
            path = row[0]
            book_hash = row[1]
            print(f"Path string: {repr(path)}")
            print(f"Book Hash: {book_hash}")
            print(f"Path hex: {path.encode('utf-8').hex()}")

            # Check length of the string
            print(f"Path length (chars): {len(path)}")

            # Check if it contains any non-printable chars or weirdness
            for i, c in enumerate(path):
                if ord(c) < 32 or ord(c) > 126:
                    print(f"Weird char at index {i}: {repr(c)} (code: {ord(c)})")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check_path_hex())
