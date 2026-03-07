import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from dotenv import load_dotenv

# Import ALL models to ensure relationships are loaded
try:
    import models.agent_models  # noqa: F401
    import models.library  # noqa: F401
    import models.publication_models  # noqa: F401
    import models.user_models  # noqa: F401
except ImportError:
    pass

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library import SeriesMetadata
from utils.helpers import generar_slug_from_meta

load_dotenv()


async def repair_slugs():
    print("🛠️ Reparando slugs y nombres en inglés faltantes...")
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://zeepub:zeepub@localhost:5432/zeepub"

    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            # 1. Buscar series con slug nulo
            stmt = select(SeriesMetadata).where(SeriesMetadata.slug.is_(None))
            result = await session.execute(stmt)
            series_list = result.scalars().all()

            print(f"Encontradas {len(series_list)} series sin slug.")

            updates = 0
            for s in series_list:
                # Intentar generar slug
                new_slug = generar_slug_from_meta({"series": s.series_name})

                if new_slug:
                    s.slug = new_slug
                    updates += 1

            if updates > 0:
                await session.flush()
                await session.commit()
                print(f"✅ Se han reparado {updates} slugs.")
            else:
                print("No se pudieron generar slugs para las series encontradas o no había ninguna vacía.")

            # 2. Resumen final
            res = await session.execute(select(SeriesMetadata).where(SeriesMetadata.slug.is_(None)))
            restantes = len(res.scalars().all())
            print(f"Series restantes sin slug: {restantes}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(repair_slugs())
