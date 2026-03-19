import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LibrarySource

load_dotenv()


async def ensure_source():
    await pg_manager.initialize()
    path = os.getenv("LIBRARY_PATH", r"C:\Users\charl\Downloads\epub")

    async with pg_manager.begin() as session:
        # Verificar si existe
        res = await session.execute(select(LibrarySource).where(LibrarySource.path == path))
        source = res.scalar_one_or_none()

        if not source:
            print(f"Añadiendo fuente: {path}")
            new_source = LibrarySource(name="Local Download", path=path)
            session.add(new_source)
            print("Fuente añadida.")
        else:
            print(f"La fuente ya existe en DB: {source.path}")


if __name__ == "__main__":
    asyncio.run(ensure_source())
