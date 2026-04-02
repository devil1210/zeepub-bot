import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv
from sqlalchemy import text

# Importar todos los modelos para asegurar que SQLAlchemy resuelva relaciones
from core.db_manager_pg import pg_manager

load_dotenv()


async def patch_db():
    print("Iniciando parche de base de datos para aumentar longitud de slug...")

    # Manejo de DATABASE_URL para local/docker
    db_url = os.environ.get("DATABASE_URL", "")
    if "@db:5432" in db_url:
        os.environ["DATABASE_URL"] = db_url.replace("@db:5432", "@localhost:5432")

    try:
        await pg_manager.initialize()
        async with pg_manager.engine.begin() as conn:
            # Aumentar longitud de slug en series_metadata
            await conn.execute(text("ALTER TABLE series_metadata ALTER COLUMN slug TYPE VARCHAR(512);"))
            print("✅ Columna 'slug' en 'series_metadata' aumentada a 512 caracteres.")

    except Exception as e:
        print(f"❌ Error aplicando parche: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(patch_db())
