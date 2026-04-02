
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def check_columns():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found")
        return
        
    # Ajustar para ejecución local si es necesario
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    if "@db:" in db_url:
        db_url = db_url.replace("@db:", "@localhost:")
        
    print(f"Connecting to: {db_url}")
    engine = create_async_engine(db_url)
    
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'duplicate_books'
        """))
        columns = result.fetchall()
        print("\nColumnas encontradas en 'duplicate_books':")
        for col in columns:
            print(f"- {col[0]}: {col[1]}")
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_columns())
