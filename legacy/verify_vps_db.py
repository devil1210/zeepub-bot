import asyncio
import os
from sqlalchemy import text
from core.db_manager_pg import pg_manager
from dotenv import load_dotenv

load_dotenv()

# Forzar conexión a localhost:5432 (el túnel al VPS)
if "DATABASE_URL" in os.environ:
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', '').replace('@db:5432', '@localhost:5432')

async def verify_db():
    try:
        await pg_manager.initialize()
        async with pg_manager.engine.connect() as conn:
            # 1. Verificar Nombre de la DB y Tablas
            res = await conn.execute(text("SELECT current_database(), current_user"))
            db_info = res.fetchone()
            print(f"--- Conectado a: {db_info} ---")

            # 2. Verificar Columnas de series_metadata
            result = await conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'series_metadata'
                ORDER BY column_name
            """))
            columns = {row[0]: row[1] for row in result}
            
            critical_cols = ['series_spanish', 'series_english', 'slug', 'author_jap', 'tags']
            print("\nEstado de columnas críticas en series_metadata:")
            for col in critical_cols:
                status = "✅ EXISTE" if col in columns else "❌ NO EXISTE"
                print(f"- {col}: {status} ({columns.get(col, 'N/A')})")
            
            # 3. Verificar conteo de series
            res_count = await conn.execute(text("SELECT COUNT(*) FROM series_metadata"))
            count = res_count.scalar()
            print(f"\nTotal de series en DB: {count}")

            # 4. Verificar si hay libros (local_books)
            res_books = await conn.execute(text("SELECT COUNT(*) FROM local_books"))
            books_count = res_books.scalar()
            print(f"Total de libros en DB: {books_count}")
            
    except Exception as e:
        print(f"Error en verificación: {e}")
    finally:
        await pg_manager.close()

if __name__ == '__main__':
    asyncio.run(verify_db())
