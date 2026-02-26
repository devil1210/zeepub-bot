import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv

from core.db_manager_pg import pg_manager
from scripts.assign_short_links import main as assign_links
from services.scanner_service import ScannerService
from services.sync_service import SyncService

load_dotenv()


async def run_sync_all():
    print("🚀 Iniciando Proceso de Sincronización Completa...")

    # Asegurar conexión local
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

    try:
        # 1. Escaneo de libros
        print("\n--- 1. Escaneando Directorio de Libros ---")
        libs_config = os.environ.get("LOCAL_LIBRARIES", "{}")
        scanner = ScannerService(libraries_config_json=libs_config)
        scan_results = await scanner.sync_all(force_scan=False)
        print(f"Resultado del escaneo: {scan_results}")

        # 2. Asignación de short_links deterministas
        print("\n--- 2. Asignando Short Links a nuevos libros ---")
        await assign_links()

        # 3. Sincronización a Supabase
        print("\n--- 3. Sincronizando con Supabase ---")
        sync_results = await SyncService.sync_library_to_cloud()

        if sync_results.get("success"):
            print(f"✅ Sincronización exitosa: {sync_results.get('message')}")
            print(f"Estadísticas: {sync_results.get('stats')}")
        else:
            print(f"❌ Error en sincronización: {sync_results.get('message')}")

    except Exception as e:
        print(f"❌ Error crítico en el proceso: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(run_sync_all())
