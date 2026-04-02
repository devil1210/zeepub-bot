import asyncio
from core.db_manager_pg import pg_manager
from sqlalchemy import text
from dotenv import load_dotenv
load_dotenv()
import os
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '').replace('@db:5432', '@localhost:5432')

async def add_col():
    try:
        await pg_manager.initialize()
        async with pg_manager.engine.begin() as conn:
            await conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS short_link VARCHAR(20) UNIQUE;"))
        print('Column added successfully.')
    except Exception as e:
        print(f"Error adding column: {e}")

if __name__ == '__main__':
    asyncio.run(add_col())
