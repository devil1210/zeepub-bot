import asyncio
import logging
import sys
import os

# Configurar logging para ver todo en consola sin emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("ScanTest")

async def run_test():
    print("\n--- Iniciando Escaneo con ScannerService ---")
    
    try:
        # Asegurar que el directorio raíz esté en el path
        sys.path.append(os.getcwd())
        
        # Importaciones necesarias
        from core.db_manager_pg import pg_manager
        from models.base import Base
        # Importar modelos para que se registren en Base.metadata
        import models.library_models 
        import models.user_models
        import models.translators_models
        from services.scanner_service import ScannerService
        
        # 1. Asegurar que las tablas existan (Postgres)
        print("Paso 1: Inicializando motor y creando tablas si no existen...")
        await pg_manager.initialize()
        # Nota: En desarrollo local usamos Base.metadata.create_all para asegurar esquema
        async with pg_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # 2. Inicializar ScannerService
        print("Paso 2: Inicializando ScannerService...")
        scanner_service = ScannerService()
        
        # 3. Ejecutar escaneo completo
        print("Paso 3: Ejecutando sync_all(force_scan=True)...")
        results = await scanner_service.sync_all(force_scan=True)
        
        if results:
            print("\n--- Resultados del Escaneo ---")
            print(f"Fuentes escaneadas: {results.get('sources_scanned', 0)}")
            print(f"Total libros procesados: {results.get('total_scanned', 0)}")
            print(f"Libros añadidos: {results.get('added', 0)}")
            print(f"Libros actualizados: {results.get('updated', 0)}")
            print(f"Duplicados: {results.get('duplicates', 0)}")
            print(f"Fallidos: {results.get('failed', 0)}")
            # touched_series_hashes puede ser un set o una lista vacía
            hashes = results.get('touched_series_hashes', [])
            print(f"Series tocadas: {len(hashes) if hashes else 0}")
        else:
            print("\nEl escaneo no devolvió resultados o ya había uno en curso.")
            
    except Exception as e:
        print(f"\nError fatal durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nPrueba interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError al ejecutar asyncio: {e}")
