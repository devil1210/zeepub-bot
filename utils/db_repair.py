import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from models.base import Base
from models.user_models import UserLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_REPAIR")


async def repair_database():
    logger.info("Starting Emergency Database Repair...")
    await pg_manager.initialize()

    async with pg_manager.engine.begin() as conn:
        # 1. Ensure tables exist
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables checked/created.")

    async with pg_manager.get_session() as session:
        # 2. Add missing columns to user_levels (Manual SQL to be safe)
        columns = [
            ("color", "VARCHAR(20) DEFAULT '#607D8B'"),
            ("ui_glass_blur", "INTEGER DEFAULT 12"),
            ("ui_cover_width", "INTEGER DEFAULT 120"),
            ("ui_accent_opacity", "INTEGER DEFAULT 20"),
            ("panel_transparency", "INTEGER DEFAULT 60"),
            ("price", "INTEGER DEFAULT 0"),
            ("early_access", "BOOLEAN DEFAULT FALSE"),
            ("custom_themes", "BOOLEAN DEFAULT FALSE"),
        ]

        for col_name, col_type in columns:
            try:
                check_sql = text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name='user_levels' AND column_name='{col_name}'"
                )
                res = await session.execute(check_sql)
                if not res.scalar():
                    logger.info(f"Adding column {col_name} to user_levels...")
                    await session.execute(
                        text(f"ALTER TABLE user_levels ADD COLUMN {col_name} {col_type}")
                    )
            except Exception as e:
                logger.error(f"Error adding column {col_name}: {e}")

        await session.commit()

        # 3. Force seed levels 1-6
        logger.info("Upserting mandatory user levels...")
        levels = [
            UserLevel(
                id=1,
                name="Administrador",
                priority=100,
                color="#FF5252",
                price=0,
                daily_downloads=999,
                has_mini_app_access=True,
                early_access=True,
                custom_themes=True,
                ui_theme="dark",
            ),
            UserLevel(
                id=2,
                name="Staff",
                priority=90,
                color="#7C4DFF",
                price=0,
                daily_downloads=999,
                has_mini_app_access=True,
                early_access=True,
                custom_themes=True,
                ui_theme="dark",
            ),
            UserLevel(
                id=3,
                name="Premium",
                priority=50,
                color="#FFD740",
                price=499,
                daily_downloads=50,
                has_mini_app_access=True,
                early_access=False,
                custom_themes=True,
                ui_theme="dark",
            ),
            UserLevel(
                id=4,
                name="VIP",
                priority=40,
                color="#69F0AE",
                price=999,
                daily_downloads=20,
                has_mini_app_access=True,
                early_access=False,
                custom_themes=True,
                ui_theme="dark",
            ),
            UserLevel(
                id=5,
                name="Patrocinador",
                priority=20,
                color="#E0E0E0",
                price=0,
                daily_downloads=10,
                has_mini_app_access=True,
                early_access=False,
                custom_themes=False,
                ui_theme="dark",
            ),
            UserLevel(
                id=6,
                name="Lector",
                priority=10,
                color="#607D8B",
                price=0,
                daily_downloads=5,
                has_mini_app_access=True,
                early_access=False,
                custom_themes=False,
                ui_theme="dark",
            ),
        ]

        for lvl in levels:
            await session.merge(lvl)

        await session.commit()

    logger.info("Database repair completed successfully!")
    await pg_manager.engine.dispose()


if __name__ == "__main__":
    asyncio.run(repair_database())
