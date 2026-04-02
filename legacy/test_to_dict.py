import asyncio
import os
import sys
from sqlalchemy import select

# Añadir directorio actual al path
sys.path.append(os.getcwd())

from core.db_manager_pg import pg_manager
from models.library_models import SeriesMetadata

async def verify_to_dict():
    # Inicializar el gestor de base de datos
    await pg_manager.initialize()
    
    async with pg_manager.get_session() as session:
        # Buscar una serie cualquiera
        stmt = select(SeriesMetadata).limit(1)
        res = await session.execute(stmt)
        series = res.scalars().first()
        
        if not series:
            print("No se encontró ninguna serie para probar.")
            return

        d = series.to_dict()
        print(f"Serie: {series.series_name}")
        print(f"Diccionario keys: {list(d.keys())}")
        
        # Verificar si 'series_name' está en el dict (es la hybrid property)
        if "series_name" in d:
            print("✅ 'series_name' (hybrid property) detectada en to_dict()")
        else:
            print("❌ 'series_name' NO detectada en to_dict()")
        
        # Verificar si 'slug' está (columna normal)
        if "slug" in d:
            print("✅ 'slug' (columna) detectada en to_dict()")
            
if __name__ == "__main__":
    asyncio.run(verify_to_dict())
