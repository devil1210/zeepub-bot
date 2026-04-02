
import asyncio
import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

os.environ["DATABASE_URL"] = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

from services.library_service import LibraryService
from core.db_manager_pg import pg_manager

async def test_volumes():
    h = "ce88a1afd0700bbfaac95c29f7e3950db16be87229feef011e76cb468d9bd0232"
    volumes = await LibraryService.get_series_volumes(h)
    print(f"Retrieved {len(volumes)} volumes")
    for v in volumes:
        print(f"Title: {v.get('title')} | Downloads: {v.get('download_count')} | Rating: {v.get('rating')}")

if __name__ == "__main__":
    asyncio.run(test_volumes())
