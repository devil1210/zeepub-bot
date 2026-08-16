import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from sqlalchemy import text

from core.db_manager_pg import pg_manager

load_dotenv()


async def patch_db():
    print("Iniciando migración de campos de Facebook (Álbumes y Posts)...")

    # Manejo de DATABASE_URL para local/docker
    db_url = os.environ.get("DATABASE_URL", "")
    if "@db:5432" in db_url:
        os.environ["DATABASE_URL"] = db_url.replace("@db:5432", "@localhost:5432")

    try:
        await pg_manager.initialize()
        async with pg_manager.engine.begin() as conn:
            # 1. Tabla series / series_metadata
            for tbl in ["series", "series_metadata"]:
                try:
                    await conn.execute(
                        text(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS fb_album_id VARCHAR(128);")
                    )
                    print(f"✅ Columna 'fb_album_id' asegurada en '{tbl}'.")
                except Exception as ex:
                    print(f"⚠️ Tabla '{tbl}' no modificada: {ex}")

            # 2. Tabla books / local_books
            for tbl in ["books", "local_books"]:
                try:
                    await conn.execute(
                        text(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS fb_post_id VARCHAR(128);")
                    )
                    await conn.execute(
                        text(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS fb_photo_id VARCHAR(128);")
                    )
                    print(f"✅ Columnas 'fb_post_id' y 'fb_photo_id' aseguradas en '{tbl}'.")
                except Exception as ex:
                    print(f"⚠️ Tabla '{tbl}' no modificada: {ex}")

    except Exception as e:
        print(f"❌ Error aplicando migración: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(patch_db())
