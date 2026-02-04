import logging
from typing import Any

from sqlalchemy import func, select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, UserRating
from models.user_models import User, UserLevel
from repositories.download_repository import download_repo

logger = logging.getLogger(__name__)


class StatsService:
    """
    Service for calculating various system and user statistics.
    """

    async def get_admin_stats(self) -> dict[str, Any]:
        """
        Returns a comprehensive dictionary of system-wide statistics.
        """
        async with pg_manager.get_session() as session:
            try:
                # 1. User Stats
                user_count = (await session.execute(select(func.count(User.id)))).scalar() or 0

                # 2. Book Stats
                book_count = (await session.execute(select(func.count(LocalBook.id)))).scalar() or 0

                # 3. Downloads (Global)
                total_downloads = await download_repo.get_global_total_downloads()

                # 4. Rating Stats
                rating_count = (
                    await session.execute(select(func.count(UserRating.id)))
                ).scalar() or 0

                # 5. User Distribution by Level
                level_dist_stmt = (
                    select(UserLevel.name, func.count(User.id))
                    .join(User, User.level_id == UserLevel.id)
                    .group_by(UserLevel.name)
                )
                level_dist = (await session.execute(level_dist_stmt)).fetchall()

                return {
                    "users": {
                        "total": user_count,
                        "distribution": {name: count for name, count in level_dist},
                    },
                    "library": {
                        "total_books": book_count,
                        "total_downloads": total_downloads,
                        "total_ratings": rating_count,
                    },
                    "success": True,
                }
            except Exception as e:
                logger.error(f"StatsService error: {e}")
                return {"success": False, "error": str(e)}

    async def get_user_stats(self, user_id: int) -> dict[str, Any]:
        """
        Returns statistics for a specific user.
        """
        try:
            user_downloads = await download_repo.get_user_download_count(user_id)
            # Add more user specific stats here
            return {"user_id": user_id, "downloads": user_downloads, "success": True}
        except Exception as e:
            logger.error(f"StatsService user error ({user_id}): {e}")
            return {"success": False, "error": str(e)}


stats_service = StatsService()
