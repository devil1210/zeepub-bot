
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def diag():
    DATABASE_URL = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            db_name = await conn.execute(text("SELECT current_database();"))
            print(f"Base de datos actual: {db_name.scalar()}")
            
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users';
            """))
            print("Columnas en 'users':")
            for row in result:
                print(f"- {row[0]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(diag())
