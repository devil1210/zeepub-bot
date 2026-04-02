
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def inspect_db():
    DATABASE_URL = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users';
            """))
            columns = result.fetchall()
            print("\n--- Columnas en tabla 'users' ---")
            for col in columns:
                print(f"- {col[0]} ({col[1]})")
            
            # Ver si hay una tabla en otro schema
            result = await conn.execute(text("SELECT current_schema();"))
            print(f"Schema actual: {result.scalar()}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect_db())
