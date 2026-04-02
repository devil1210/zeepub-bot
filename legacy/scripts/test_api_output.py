import asyncio
import json
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from config.config_settings import config

if "db:5432" in config.DATABASE_URL:
    config.DATABASE_URL = config.DATABASE_URL.replace("db:5432", "localhost:5432")

from services.library_service import LibraryService


async def test_api():
    # ID from previous search
    book_id = 1707
    book = await LibraryService.get_book_by_id(book_id)
    if book:
        print("API Output for Book 1707:")
        print(json.dumps(book, indent=2))
    else:
        print(f"Book {book_id} not found via LibraryService.")


if __name__ == "__main__":
    asyncio.run(test_api())
