import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


async def patch_supabase_schema():
    print("🚀 Iniciando parche de esquema en Supabase...")

    # Buscamos la URL de Supabase.
    # Priorizamos una variable específica si existe, o usamos la DATABASE_URL si apunta a Supabase
    supabase_db_url = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")

    if not supabase_db_url or "supabase.co" not in supabase_db_url:
        print("❌ Error: No se encontró una URL de base de datos de Supabase válida.")
        print("Asegúrate de que DATABASE_URL o SUPABASE_DB_URL apunten a tu instancia de Supabase.")
        return

    # Asegurar que la URL sea compatible con asyncpg
    if supabase_db_url.startswith("postgres://"):
        supabase_db_url = supabase_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif supabase_db_url.startswith("postgresql://") and "+asyncpg" not in supabase_db_url:
        supabase_db_url = supabase_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("Conectando a Supabase...")

    try:
        engine = create_async_engine(supabase_db_url)
        async with engine.begin() as conn:
            print("--- Aplicando cambios en series_metadata ---")

            # 1. Aumentar columnas de series_metadata
            columns_to_fix = [
                ("series_name", "VARCHAR(512)"),
                ("series_spanish", "VARCHAR(512)"),
                ("series_english", "VARCHAR(512)"),
                ("slug", "VARCHAR(512)"),
                ("book_type", "VARCHAR(255)"),
            ]

            for col, col_type in columns_to_fix:
                try:
                    await conn.execute(text(f"ALTER TABLE series_metadata ALTER COLUMN {col} TYPE {col_type};"))
                    print(f"✅ Columna '{col}' actualizada a {col_type}")
                except Exception as e:
                    print(f"⚠️ No se pudo actualizar '{col}': {e}")

            # 2. Asegurar columnas nuevas en local_books
            print("--- Verificando columnas en local_books ---")
            lb_columns = [
                ("series_spanish", "VARCHAR(512)"),
                ("series_english", "VARCHAR(512)"),
                ("spanish_title", "VARCHAR(512)"),
                ("romaji_title", "VARCHAR(512)"),
                ("english_title", "VARCHAR(512)"),
                ("is_uncensored", "INTEGER DEFAULT 0"),
                ("color_mode", "VARCHAR(50)"),
                ("short_link", "VARCHAR(255)"),
            ]

            for col, col_type in lb_columns:
                try:
                    await conn.execute(text(f"ALTER TABLE local_books ADD COLUMN IF NOT EXISTS {col} {col_type};"))
                    # Si ya existía, forzar el tipo por si acaso
                    if "VARCHAR" in col_type:
                        await conn.execute(text(f"ALTER TABLE local_books ALTER COLUMN {col} TYPE {col_type};"))
                    print(f"✅ Columna '{col}' verificada/actualizada.")
                except Exception as e:
                    print(f"⚠️ No se pudo verificar columna '{col}': {e}")

            print("\n✅ Esquema de Supabase actualizado correctamente.")

        await engine.dispose()
    except Exception as e:
        print(f"❌ Error crítico al conectar/parchear Supabase: {e}")


if __name__ == "__main__":
    asyncio.run(patch_supabase_schema())
