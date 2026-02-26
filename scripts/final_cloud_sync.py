import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv

# Import ALL models
try:
    import models.agent_models  # noqa: F401
    import models.library_models  # noqa: F401
    import models.publication_models  # noqa: F401
    import models.user_models  # noqa: F401
except ImportError:
    pass

from core.db_manager_pg import pg_manager
from services.sync_service import SyncService

load_dotenv()


async def run_final_sync():
    print("🚀 Inciando Sincronización Final a Supabase...")

    # Asegurar configuración
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

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
    # Aumentar timeout si es necesario mediante settings de asyncpg si fuera accesible,
    # pero intentaremos ejecución normal primero.
    asyncio.run(run_final_sync())
