import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv
from sqlalchemy import text

from core.db_manager_pg import pg_manager

load_dotenv()


async def check_columns():
    print("Verificando columnas en la base de datos local...")

    # Usar credenciales de docker-compose para local
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

    try:
        await pg_manager.initialize()
        async with pg_manager.engine.connect() as conn:
            # Listar tablas
            res = await conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [r[0] for r in res.fetchall()]
            print(f"Tablas encontradas: {tables}")

            if "series_metadata" in tables:
                res = await conn.execute(
                    text(
                        "SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'series_metadata'"
                    )
                )
                cols = res.fetchall()
                print("\nColumnas en 'series_metadata':")
                for col in cols:
                    print(f" - {col[0]} ({col[1]}, {col[2]})")
            else:
                print("❌ La tabla 'series_metadata' NO existe en la base de datos local.")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check_columns())
