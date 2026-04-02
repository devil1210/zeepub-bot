
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check():
    await pg_manager.initialize()
    try:
        async with pg_manager.get_session() as session:
            res = await session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'series_metadata'"))
            cols = sorted([row[0] for row in res])
            print("Total columns in series_metadata:", len(cols))
            for c in cols:
                print(f"- {c}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(check())
