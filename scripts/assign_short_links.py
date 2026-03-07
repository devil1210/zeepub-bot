import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

# Import ALL models to ensure SQLAlchemy resolves all relationships
try:
    import models.agent_models  # noqa: F401
    import models.library  # noqa: F401
    import models.publication_models  # noqa: F401
    import models.user_models  # noqa: F401
except ImportError:
    pass

from core.db_manager_pg import pg_manager
from models.library import LocalBook
from utils.helpers import generate_short_link


async def main():
    print("Iniciando asignación de short_links estables basados en hash...")

    # Forzar uso de localhost para ejecución local si falla el DNS de Docker
    if "DATABASE_URL" in os.environ:
        os.environ["DATABASE_URL"] = os.environ["DATABASE_URL"].replace("@db:5432", "@localhost:5432")

    try:
        await pg_manager.initialize()
    except Exception as e:
        print(f"Error de conexión: {e}")
        print("Intentando con fallback a localhost...")
        # Intentar forzar la URL si no estaba en env
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/zeepub_bot"
        await pg_manager.initialize()

    async with pg_manager.get_session() as session:
        # Buscamos todos los libros
        stmt = select(LocalBook)
        result = await session.execute(stmt)
        books = result.scalars().all()

        if not books:
            print("No se encontraron libros en la base de datos.")
            return

        print(f"✅ Se encontraron {len(books)} libros.")
        print("Procesando en lotes de 20...")

        total_updated = 0
        for i in range(0, len(books), 20):
            batch = books[i : i + 20]
            batch_updates = 0
            for book in batch:
                if not book.book_hash:
                    continue
                new_link = generate_short_link(book.book_hash)
                if book.short_link != new_link:
                    book.short_link = new_link
                    batch_updates += 1

            if batch_updates > 0:
                await session.flush()
                await session.commit()  # Commit each batch for safety and visibility
                total_updated += batch_updates
                print(
                    f"📦 Lote {i // 20 + 1} completado. Actualizados: {batch_updates} (Total: {total_updated}/{len(books)})"
                )
            else:
                print(f"⏭️ Lote {i // 20 + 1} saltado (sin cambios).")

        print(f"\n✨ Proceso terminado. Se actualizaron {total_updated} short_links.")

    await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
