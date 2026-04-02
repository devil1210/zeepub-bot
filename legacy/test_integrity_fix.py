import asyncio
import uuid
from sqlalchemy import text
from core.db_manager_pg import pg_manager
from models.library import Series

async def test_insert():
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            new_series = Series(
                id=str(uuid.uuid4()),
                name="Test Series " + str(uuid.uuid4())[:8],
                rating_average=4.5,
                rating_count=10,
                book_count=5
            )
            session.add(new_series)
            await session.commit()
            print("INSERT_SUCCESS")
            
            # Clean up
            await session.delete(new_series)
            await session.commit()
            print("CLEANUP_SUCCESS")
    except Exception as e:
        print(f"INSERT_FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_insert())
