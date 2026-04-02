
import asyncio
import os
import sys
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager

async def main():
    try:
        async with pg_manager.get_session() as s:
            print("Inspeccionando columnas de 'duplicate_books'...")
            res = await s.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'duplicate_books'
                ORDER BY ordinal_position
            """))
            columns = res.fetchall()
            if not columns:
                print("La tabla 'duplicate_books' no existe o no tiene columnas.")
            else:
                for row in columns:
                    print(f"- {row[0]} ({row[1]})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
