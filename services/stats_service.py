import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from core.db_manager_pg import pg_manager
from models.download_models import DownloadHistory
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
                user_count = (await session.execute(select(func.count(User.telegram_id)))).scalar() or 0

                # 2. Book Stats
                book_count = (await session.execute(select(func.count(LocalBook.id)))).scalar() or 0

                # 3. Downloads (Global)
                total_downloads = await download_repo.get_global_total_downloads()

                # 4. Rating Stats
                rating_count = (await session.execute(select(func.count(UserRating.id)))).scalar() or 0

                # 5. User Distribution by Level
                level_dist_stmt = (
                    select(UserLevel.name, func.count(User.telegram_id))
                    .join(User, User.level_id == UserLevel.id)
                    .group_by(UserLevel.name)
                )
                level_dist = (await session.execute(level_dist_stmt)).fetchall()

                return {
                    "users": {
                        "total": user_count,
                        "distribution": dict(level_dist),
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


# --- Top-level functions for legacy compatibility and scheduled tasks ---


async def record_activity(user_id: int, action: str):
    """
    Registers a user activity for stats purposes.
    Currently, download actions are already tracked in download_history.
    """
    logger.debug(f"Activity recorded for user {user_id}: {action}")
    # In the future, we could store this in a dedicated activity_log table.
    pass


async def get_daily_stats() -> dict[str, Any]:
    """
    Returns statistics for the current day.
    """
    async with pg_manager.get_session() as session:
        try:
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # 1. Total downloads today
            total_downloads = (
                await session.execute(
                    select(func.count(DownloadHistory.id)).where(DownloadHistory.downloaded_at >= today_start)
                )
            ).scalar() or 0

            # 2. Unique users today
            unique_users = (
                await session.execute(
                    select(func.count(func.distinct(DownloadHistory.user_id))).where(
                        DownloadHistory.downloaded_at >= today_start
                    )
                )
            ).scalar() or 0

            # 3. Breakdown by role
            role_breakdown_stmt = (
                select(UserLevel.name, func.count(DownloadHistory.id))
                .join(User, DownloadHistory.user_id == User.telegram_id)
                .join(UserLevel, User.level_id == UserLevel.id)
                .where(DownloadHistory.downloaded_at >= today_start)
                .group_by(UserLevel.name)
            )
            role_breakdown = (await session.execute(role_breakdown_stmt)).fetchall()

            return {
                "total_downloads": total_downloads,
                "unique_users": unique_users,
                "by_role": dict(role_breakdown),
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {
                "total_downloads": 0,
                "unique_users": 0,
                "by_role": {},
                "success": False,
                "error": str(e),
            }


async def reset_stats():
    """
    Resets daily statistics if there are any temporary counters.
    Download history is immutable, so this is mostly for other metrics.
    """
    logger.info("Daily stats reset executed.")
    pass


async def get_stats_summary(period: str = "day") -> dict[str, Any]:
    """
    Get stats for a specific period: day, month, year, all.
    """
    async with pg_manager.get_session() as session:
        try:
            now = datetime.utcnow()
            start_date = None

            if period == "day":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "month":
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == "year":
                start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            # if period == "all", start_date remains None

            # 1. Downloads
            if start_date:
                downloads_stmt = select(func.count(DownloadHistory.id)).where(
                    DownloadHistory.downloaded_at >= start_date
                )
                users_stmt = select(func.count(func.distinct(DownloadHistory.user_id))).where(
                    DownloadHistory.downloaded_at >= start_date
                )
            else:
                downloads_stmt = select(func.count(DownloadHistory.id))
                users_stmt = select(func.count(func.distinct(DownloadHistory.user_id)))

            total_downloads = (await session.execute(downloads_stmt)).scalar() or 0
            unique_users = (await session.execute(users_stmt)).scalar() or 0

            # New users (registrations)
            new_users = 0
            if hasattr(User, "created_at"):
                if start_date:
                    new_stmt = select(func.count(User.telegram_id)).where(User.created_at >= start_date)
                else:
                    new_stmt = select(func.count(User.telegram_id))
                new_users = (await session.execute(new_stmt)).scalar() or 0

            return {
                "total_downloads": total_downloads,
                "unique_users": unique_users,
                "new_users": new_users,
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error getting stats summary ({period}): {e}")
            return {
                "total_downloads": 0,
                "unique_users": 0,
                "new_users": 0,
                "success": False,
            }
