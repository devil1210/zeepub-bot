import asyncio
import logging

from sqlalchemy import text

from core.db_manager_pg import pg_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_levels():
    async with pg_manager.get_session() as session:
        # Check if levels already exist
        res = await session.execute(text("SELECT count(*) FROM user_levels"))
        count = res.scalar()

        if count > 0:
            logger.info(f"Database already has {count} levels. Skipping seed.")
            return

        logger.info("Seeding default user levels...")

        levels = [
            (
                1,
                "Administrador",
                100,
                "#FF4B4B",
                0.0,
                -1,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
            ),
            (
                2,
                "Staff",
                90,
                "#4ECDC4",
                0.0,
                20,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
            ),
            (
                3,
                "Premium",
                80,
                "#FFD93D",
                0.0,
                10,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
            ),
            (
                4,
                "VIP",
                70,
                "#1A5F7A",
                0.0,
                7,
                True,
                True,
                True,
                True,
                True,
                True,
                True,
                False,
                False,
                True,
            ),
            (
                5,
                "Patrocinador",
                60,
                "#FFFFFF",
                0.0,
                5,
                True,
                True,
                True,
                True,
                True,
                False,
                True,
                False,
                False,
                True,
            ),
            (
                6,
                "Gratis",
                0,
                "#888888",
                0.0,
                3,
                True,
                True,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
            ),
        ]

        for lvl in levels:
            await session.execute(
                text("""
                INSERT INTO user_levels (
                    id, name, priority, color, price, daily_downloads,
                    can_download, can_read, has_mini_app_access,
                    has_library_access, can_request_books, can_upload_epub,
                    early_access, custom_themes, allow_theme_templates, show_recommendations
                ) VALUES (
                    :id, :name, :priority, :color, :price, :daily_downloads,
                    :can_download, :can_read, :has_mini_app_access,
                    :has_library_access, :can_request_books, :can_upload_epub,
                    :early_access, :custom_themes, :allow_theme_templates, :show_recommendations
                )
            """),
                {
                    "id": lvl[0],
                    "name": lvl[1],
                    "priority": lvl[2],
                    "color": lvl[3],
                    "price": lvl[4],
                    "daily_downloads": lvl[5],
                    "can_download": lvl[6],
                    "can_read": lvl[7],
                    "has_mini_app_access": lvl[8],
                    "has_library_access": lvl[9],
                    "can_request_books": lvl[10],
                    "can_upload_epub": lvl[11],
                    "early_access": lvl[12],
                    "custom_themes": lvl[13],
                    "allow_theme_templates": lvl[14],
                    "show_recommendations": lvl[15],
                },
            )

        logger.info("Default levels seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed_levels())
