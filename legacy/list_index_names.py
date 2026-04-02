
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_indices():
    DATABASE_URL = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            for table in ['local_books', 'download_history', 'series_metadata']:
                print(f"\n--- Índices en '{table}' ---")
                res = await conn.execute(text(f"SELECT indexname FROM pg_indexes WHERE tablename = '{table}';"))
                for row in res:
                    print(f"  - {row[0]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_indices())
