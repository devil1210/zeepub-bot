import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

# Importar Base de los modelos para la creación del esquema
# Asegurarse de que el path del proyecto esté en sys.path
sys.path.append(os.getcwd())
from models.base import Base

# Importar todos los modelos para que Base los conozca

load_dotenv()


async def sync_supabase_v4():
    print(f"{'=' * 60}")
    print("🚀 [SUPABASE V4 SYNC] Iniciando sincronización de esquema...")
    print(f"{'=' * 60}")

    supabase_url = os.environ.get("SUPABASE_URL")
    db_pass = os.environ.get("SUPABASE_DB_PASSWORD")

    if not supabase_url or not db_pass:
        print("❌ Error: Faltan SUPABASE_URL o SUPABASE_DB_PASSWORD en el .env")
        return

    # Extraer el ID del proyecto de la URL
    project_ref = supabase_url.split("//")[1].split(".")[0]

    # URL directa (asíncrona)
    supabase_db_url = f"postgresql+asyncpg://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres"

    print(f"📡 Conectando a Supabase ({project_ref})...")

    try:
        engine = create_async_engine(supabase_db_url, echo=False)

        async with engine.begin() as conn:
            print("🧹 Limpiando esquema anterior (V3) en Supabase...")
            # Como es un RESTART, eliminamos las tablas conflictivas si existen
            # Se hace con precaución, pero es necesario para cambiar PKs de BigInt a UUID
            await conn.execute(text("DROP TABLE IF EXISTS download_logs CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS books CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS series CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS library_sources CASCADE;"))
            # Nota: users y user_levels se mantienen si no hay cambios rupturistas en PKs,
            # pero aquí el plan es UUID en user_levels.
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS user_levels CASCADE;"))

            print("🏗️  Creando nuevo esquema V4 (UUID, Async)...")
            # Usar la metadata de SQLAlchemy para crear las tablas
            await conn.run_sync(Base.metadata.create_all)

            print("✅ Esquema V4 desplegado exitosamente en Supabase.")

        await engine.dispose()
    except Exception as e:
        print(f"❌ Error crítico en sincronización: {e}")


from sqlalchemy import text

if __name__ == "__main__":
    asyncio.run(sync_supabase_v4())
