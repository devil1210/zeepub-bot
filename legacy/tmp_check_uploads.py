
import asyncio
from sqlalchemy import text
from core.db_manager_pg import pg_manager

async def check():
    await pg_manager.initialize()
    try:
        async with pg_manager.get_session() as session:
            res = await session.execute(text("SELECT count(*) FROM upload_books"))
            count = res.scalar()
            print(f"UploadBook count: {count}")
            
            res = await session.execute(text("SELECT id, telegram_id, original_filename, created_at FROM upload_books ORDER BY created_at DESC LIMIT 5"))
            for row in res:
                print(f"Record: {row}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(check())
