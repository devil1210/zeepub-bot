import asyncio
import os
import sys

# Patch DATABASE_URL before any imports
# We are currently in the project root c:\Users\charl\Downloads\Zeepub-bot
# The database might be reachable at localhost:5432
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/zeepub"

sys.path.append(os.getcwd())
from services.library_service import LibraryService


async def main():
    # Attempt to find a series hash for Index or something with multiple volumes
    from models.library import LocalBook
    from utils.library_db import get_session

    session = get_session()
    # Find series with most volumes
    from sqlalchemy import func, select

    stmt = (
        select(LocalBook.series_hash, func.count(LocalBook.id).label("count"))
        .group_by(LocalBook.series_hash)
        .order_by(func.count(LocalBook.id).desc())
        .limit(5)
    )
    res = session.execute(stmt).all()

    if not res:
        print("No series found")
        return

    for series_hash, count in res:
        print(f"\nSeries Hash: {series_hash} (Count: {count})")
        volumes = await LibraryService.get_series_volumes(series_hash)
        for v in volumes:
            print(
                f"  ID: {v['id']} | Title: {v['title']} | Volume: {v.get('volume')} | VolNum: {v.get('volumeNumber')} | translator: {v.get('translator')}"
            )


if __name__ == "__main__":
    asyncio.run(main())
