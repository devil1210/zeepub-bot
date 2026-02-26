import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv

# Import ALL models
try:
    import models.agent_models  # noqa: F401
    import models.library_models  # noqa: F401
    import models.publication_models  # noqa: F401
    import models.user_models  # noqa: F401
except ImportError:
    pass

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook

load_dotenv()


async def check_link():
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"
    target_link = "t9TyVfeSdP"

    print(f"🔍 Buscando short_link: {target_link}")

    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            stmt = select(LocalBook).where(LocalBook.short_link == target_link)
            result = await session.execute(stmt)
            book = result.scalar_one_or_none()

            if book:
                print("✅ Libro encontrado!")
                print(f"ID: {book.id}")
                print(f"Título: {book.title}")
                print(f"Serie: {book.series}")
                print(f"Hash: {book.book_hash}")
                print(f"Path en DB: {book.filepath}")

                # Verify path (might need adjustment if running in different env)
                path = book.filepath
                if not os.path.exists(path):
                    # Try local relative path if it's a volume mount
                    print(f"❓ No existe en path absoluto: {path}")
                    # Look for it relative to HOST_LIB_PATH from .env
                    host_lib = os.environ.get("HOST_LIB_PATH")
                    if host_lib:
                        print(f"Probar con HOST_LIB_PATH: {host_lib}")
                else:
                    print("📂 Archivo encontrado en disco.")

            else:
                print(f"❌ No se encontró ningún libro con short_link: {target_link}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(check_link())
