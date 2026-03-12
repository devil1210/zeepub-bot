import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def sync_supabase_schema():
    print("Sincronizando esquema con Supabase...")

    supabase_url = os.environ.get("SUPABASE_URL")
    if not supabase_url:
        print("❌ Error: Faltan SUPABASE_URL en el .env")
        return

    # Extraer el ID del proyecto de la URL
    project_ref = supabase_url.split("//")[1].split(".")[0]

    # Forzar conexión directa a Supabase
    db_pass = os.environ.get("SUPABASE_DB_PASSWORD")
    if not db_pass:
        print("❌ Error: SUPABASE_DB_PASSWORD no encontrada en el entorno.")
        return

    # Construir URL directa: postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
    supabase_db_url = f"postgresql+asyncpg://postgres:{db_pass}@db.{project_ref}.supabase.co:5432/postgres"

    print(f"Conectando a Supabase ({project_ref})...")

    try:
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(supabase_db_url)
        async with engine.begin() as conn:
            print("Aplicando cambios DDL...")
            await conn.execute(text("ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS slug VARCHAR(512);"))
            await conn.execute(text("ALTER TABLE series_metadata ALTER COLUMN slug TYPE VARCHAR(512);"))
            await conn.execute(text("ALTER TABLE series_metadata ALTER COLUMN series_english TYPE VARCHAR(512);"))
            # Sincronizar fix de duplicados
            await conn.execute(
                text(
                    "ALTER TABLE duplicate_books ADD COLUMN IF NOT EXISTS detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();"
                )
            )
            print("✅ Supabase sincronizado correctamente.")

        await engine.dispose()
    except Exception as e:
        print(f"❌ Error al sincronizar Supabase: {e}")


if __name__ == "__main__":
    asyncio.run(sync_supabase_schema())
