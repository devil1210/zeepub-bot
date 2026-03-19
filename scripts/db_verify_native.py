import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


async def verify_db():
    # URL de conexión (usamos postgresql+asyncpg para compatibilidad con el bot)
    db_url = os.getenv("DATABASE_URL")
    if "postgresql+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    # Intentar conectar a la base de datos 'postgres' primero para crear 'zeepub' si no existe
    root_url = db_url.rsplit("/", 1)[0] + "/postgres"
    engine_root = create_async_engine(root_url, isolation_level="AUTOCOMMIT")

    print(f"Intentando conectar a: {root_url}")
    try:
        async with engine_root.connect() as conn:
            # Verificar si existe la bdd 'zeepub'
            result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname='zeepub'"))
            exists = result.scalar()

            if not exists:
                print("Creando base de datos 'zeepub'...")
                await conn.execute(text("CREATE DATABASE zeepub"))
                print("Base de datos 'zeepub' creada.")
            else:
                print("La base de datos 'zeepub' ya existe.")
    except Exception as e:
        print(f"Error conectando a PostgreSQL root: {e}")
        return

    await engine_root.dispose()

    # Ahora verificar conexión a 'zeepub'
    print(f"Verificando conexión final a: {db_url}")
    engine_zeepub = create_async_engine(db_url)
    try:
        async with engine_zeepub.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("--- CONEXIÓN EXITOSA A ZEEPUB ---")

            # Intentar habilitar pgvector
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                print("Extensión 'pgvector' habilitada.")
            except Exception as ev:
                print(f"Aviso: No se pudo habilitar 'pgvector' (puede que falte en la instalación nativa): {ev}")

    except Exception as e:
        print(f"Error conectando a 'zeepub': {e}")
    finally:
        await engine_zeepub.dispose()


if __name__ == "__main__":
    asyncio.run(verify_db())
