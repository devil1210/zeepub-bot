import asyncio
import os

from dotenv import load_dotenv

load_dotenv()


async def sync_supabase_schema():
    print("Sincronizando esquema con Supabase...")

    supabase_url = os.environ.get("SUPABASE_URL")
    service_role_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_role_key:
        print("❌ Error: Faltan credenciales de Supabase en el .env")
        return

    # Extraer el ID del proyecto de la URL
    project_ref = supabase_url.split("//")[1].split(".")[0]

    # Supabase Management API o SQL API?
    # Realmente es más fácil usar el endpoint de SQL si está expuesto,
    # pero Supabase no tiene una API REST directa para SQL sin PostgREST (que es para data, no DDL).
    # Sin embargo, podemos usar la extensión de 'pg_net' o similar si estuviera,
    # pero lo más estándar es conectarse vía Postgres directo si tenemos la clave.

    # Intentemos construir la URL de conexión de Postgres para Supabase
    # postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

    # No tenemos la contraseña de la DB de Supabase explícitamente en el .env (solo service_role_key)
    # A menos que esté en una variable como DB_PASSWORD_SUPABASE o similar.

    pass_supabase = os.environ.get("SUPABASE_DB_PASSWORD")
    if not pass_supabase:
        print("⚠️ No se encontró SUPABASE_DB_PASSWORD. Buscando en otras variables...")
        # A veces se guarda en DATABASE_URL si es la de producción
        db_url = os.environ.get("DATABASE_URL", "")
        if "supabase.co" in db_url:
            print("✅ Se encontró DATABASE_URL de Supabase.")
        else:
            print("❌ No se puede sincronizar esquema de Supabase sin la contraseña de la base de datos.")
            return

    # Si llegamos aquí, intentaremos aplicar el cambio SQL usando un script que use la URL de Supabase

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    # Asegurar que la URL sea asyncpg
    supabase_db_url = os.environ.get("DATABASE_URL", "")
    if supabase_db_url.startswith("postgres://"):
        supabase_db_url = supabase_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif supabase_db_url.startswith("postgresql://") and "+asyncpg" not in supabase_db_url:
        supabase_db_url = supabase_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Conectando a Supabase ({project_ref})...")

    try:
        engine = create_async_engine(supabase_db_url)
        async with engine.begin() as conn:
            print("Aplicando cambios DDL...")
            await conn.execute(text("ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS slug VARCHAR(512);"))
            await conn.execute(text("ALTER TABLE series_metadata ALTER COLUMN slug TYPE VARCHAR(512);"))
            await conn.execute(text("ALTER TABLE series_metadata ALTER COLUMN series_english TYPE VARCHAR(512);"))
            print("✅ Supabase sincronizado correctamente.")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Error al sincronizar Supabase: {e}")


if __name__ == "__main__":
    asyncio.run(sync_supabase_schema())
