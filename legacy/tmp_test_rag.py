import asyncio
import os
import sys
import logging

# Configurar logging basico
logging.basicConfig(level=logging.INFO)

# Añadir raíz del proyecto al path
sys.path.append(os.path.abspath(os.curdir))

from services.ai.semantic_service import semantic_service
from core.db_manager_pg import pg_manager

async def test_rag():
    print("🚀 Inciando prueba de RAG/Búsqueda Semántica...")
    
    try:
        # 1. Inicializar DB
        await pg_manager.initialize()
        
        # 2. Intentar actualizar índice (esto puede fallar si no hay series o API key)
        print("\n--- Paso 1: Indexación ---")
        stats = await semantic_service.update_index()
        print(f"Stats de indexación: {stats}")
        
        # 3. Probar búsqueda
        print("\n--- Paso 2: Búsqueda Semántica ---")
        query = "busco una novela de un heroe que viaja a otro mundo con magia"
        print(f"Buscando: '{query}'")
        results = await semantic_service.search(query, limit=3)
        
        if not results:
            print("⚠️ No se encontraron resultados (¿hay series indexadas?)")
        else:
            print("✅ Resultados encontrados:")
            for i, res in enumerate(results):
                print(f"{i+1}. {res['title']} (Similitud: {res['similarity']})")
                
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
    finally:
        await pg_manager.close()

if __name__ == "__main__":
    asyncio.run(test_rag())
