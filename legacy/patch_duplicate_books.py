
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
            print("Aplicando parche a 'duplicate_books'...")
            
            # Añadir detected_at si no existe
            await s.execute(text("""
                ALTER TABLE duplicate_books 
                ADD COLUMN IF NOT EXISTS detected_at TIMESTAMP WITH TIME ZONE 
                DEFAULT CURRENT_TIMESTAMP;
            """))
            
            await s.commit()
            print("✅ Columna 'detected_at' añadida exitosamente.")
            
            # Verificar el cambio
            res = await s.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'duplicate_books' 
                AND column_name = 'detected_at'
            """))
            if res.fetchone():
                print("🔒 Verificación completada: La columna existe ahora.")
            else:
                print("❌ Error: La columna no parece haberse creado.")
                
    except Exception as e:
        print(f"Error aplicando el parche: {e}")

if __name__ == "__main__":
    asyncio.run(main())
