import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set up logging early
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", stream=sys.stdout)
logger = logging.getLogger("fix_linkage")

# Load ENV
load_dotenv(override=True)

# 1. Determine DB URL
db_url = os.environ.get("DATABASE_URL", "postgresql://zeepub:zeepub@db:5432/zeepub")
if "@db:" in db_url:
    db_url = db_url.replace("@db:", "@127.0.0.1:")
elif "@localhost:" in db_url:
    db_url = db_url.replace("@localhost:", "@127.0.0.1:")

if db_url.startswith("postgresql://"):
    db_url = "postgresql+asyncpg" + db_url[10:]
elif db_url.startswith("postgres://"):
    db_url = "postgresql+asyncpg" + db_url[8:]

os.environ["DATABASE_URL"] = db_url
logger.info(f"Targeting Database: {db_url.split('@')[-1]}")

# 2. Import components
try:
    from config.config_settings import config

    config.DATABASE_URL = db_url

    from sqlalchemy import func, select, update

    import models.communications
    import models.library

    # Import models to populate registry
    import models.users  # noqa: F401
    from core.db_manager_pg import pg_manager

    # import models.user_audit_models # Just in case
    from models.library import LocalBook, SeriesMetadata
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)


async def run_fix():
    try:
        await pg_manager.initialize()
        async with pg_manager.get_session() as session:
            # 1. Stats before
            stmt_unlinked = (
                select(func.count(LocalBook.id))
                .where(LocalBook.series_metadata_id.is_(None))
                .where(LocalBook.series_hash.is_not(None))
            )
            res_unlinked = await session.execute(stmt_unlinked)
            unlinked_before = res_unlinked.scalar()

            logger.info(f"Libros sin vincular actualmente: {unlinked_before}")

            if unlinked_before == 0:
                logger.info("✅ Ya están todos vinculados o no hay nada que vincular.")
                return

            # 2. Perform fix
            stmt_hashes = (
                select(LocalBook.series_hash)
                .where(LocalBook.series_metadata_id.is_(None))
                .where(LocalBook.series_hash.is_not(None))
                .distinct()
            )
            res_hashes = await session.execute(stmt_hashes)
            hashes = res_hashes.scalars().all()

            logger.info(f"Procesando {len(hashes)} hashes únicos...")

            updated_books = 0
            for s_hash in hashes:
                series_stmt = select(SeriesMetadata.id).where(SeriesMetadata.series_hash == s_hash)
                series_res = await session.execute(series_stmt)
                series_id = series_res.scalar_one_or_none()

                if series_id:
                    update_stmt = (
                        update(LocalBook)
                        .where(LocalBook.series_hash == s_hash)
                        .where(LocalBook.series_metadata_id.is_(None))
                        .values(series_metadata_id=series_id)
                    )
                    upd_res = await session.execute(update_stmt)
                    updated_books += upd_res.rowcount
                else:
                    logger.debug(f"Hash {s_hash} no tiene metadata correspondiente.")

            await session.commit()
            logger.info(f"✅ Vinculación finalizada. Libros actualizados: {updated_books}")

    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await pg_manager.close()


if __name__ == "__main__":
    asyncio.run(run_fix())
