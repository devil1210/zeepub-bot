
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def list_tables():
    DATABASE_URL = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_name = 'users';
            """))
            tables = result.fetchall()
            print("\n--- Tablas 'users' encontradas ---")
            for t in tables:
                print(f"- {t[0]}.{t[1]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(list_tables())
