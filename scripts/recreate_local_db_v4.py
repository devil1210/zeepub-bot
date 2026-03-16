import asyncio
import os
import sys

# Asegurar que el path del proyecto esté en sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Importar modelos para registro en metadata
from config.config_settings import config
from models.base import Base


async def recreate_local_v4():
    print("🧹 Iniciando recreación de BD local para V4...")

    # Ajustar URL para ejecución local si es necesario
    db_url = config.DATABASE_URL
    if "@db:" in db_url:
        db_url = db_url.replace("@db:", "@localhost:")
        print(f"🔄 Ajustando URL de BD para ejecución local: {db_url}")

    # Ajustar URL para asyncpg si es necesario
    if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, echo=False)

    try:
        async with engine.begin() as conn:
            print("🗑️  Eliminando tablas antiguas (Rupturista)...")
            tables = [
                "download_logs",
                "books",
                "series",
                "library_sources",
                "users",
                "user_levels",
                "app_themes",
                "agent_executions",
                "publisher_logs",
                "publication_queue",
            ]
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))

            print("🏗️  Creando nuevas tablas V4...")
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Base de datos local V4 recreada con éxito.")

    except Exception as e:
        print(f"❌ Error al recrear BD local: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(recreate_local_v4())
