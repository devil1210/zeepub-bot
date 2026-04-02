import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

from services.sync_service import SyncService

load_dotenv()


async def run_full_sync():
    print("🚀 Iniciando Sincronización Total (Local <-> Supabase)...")

    # Importar todos los modelos para asegurar que SQLAlchemy resuelva relaciones

    # Asegurar que la DB esté inicializada y los modelos cargados
    from core.db_manager_pg import pg_manager

    await pg_manager.initialize()

    # Forzar la configuración de mappers de SQLAlchemy para resolver relaciones circulares
    from sqlalchemy.orm import configure_mappers

    configure_mappers()

    # 1. Local -> Cloud (y luego Cloud -> Local via internal _pull_updates)
    result = await SyncService.sync_library_to_cloud()

    if result.get("success"):
        print(f"✅ Sincronización exitosa: {result.get('message')}")
        print(f"📊 Estadísticas: {result.get('stats')}")
    else:
        print(f"❌ Error en la sincronización: {result.get('message')}")


if __name__ == "__main__":
    asyncio.run(run_full_sync())
