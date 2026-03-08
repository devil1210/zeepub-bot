import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Bloquear uso de host Docker/db para PostgresManager local ANTES de importar config/manager
os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

from config.config_settings import config

# Sobreescribir el valor en el objeto cargado por si acaso
config.DATABASE_URL = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

# Importar modelos ANTES que el manager para resolver relaciones
try:
    import models.agent_models  # noqa: F401
    import models.communications  # noqa: F401
    import models.library  # noqa: F401
    import models.users  # noqa: F401
except ImportError:
    pass

from core.db_manager_pg import pg_manager
from services.sync_service import SyncService


async def run_final_sync():
    print("🚀 Iniciando Sincronización Final a Supabase...")
    print(f"🔗 Usando DB: {config.DATABASE_URL}")

    try:
        await pg_manager.initialize()

        print("Paso 1: Sincronizando Metadata de Series y Libros a la Nube...")
        sync_results = await SyncService.sync_library_to_cloud()

        if sync_results.get("success"):
            print(f"✅ Sincronización COMPLETADA: {sync_results.get('message')}")
            print(f"Estadísticas: {sync_results.get('stats')}")
        else:
            print(f"❌ Error en sincronización: {sync_results.get('message')}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(run_final_sync())
