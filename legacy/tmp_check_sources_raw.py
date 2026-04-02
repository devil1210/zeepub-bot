
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check():
    await pg_manager.initialize()
    try:
        async with pg_manager.get_session() as session:
            res = await session.execute(text("SELECT id, name, path FROM library_sources"))
            for row in res:
                print(f"Source: {row}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(check())
