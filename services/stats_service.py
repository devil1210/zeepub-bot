import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

STATS_FILE = os.path.join("data", "daily_stats.json")


def _load_stats() -> dict[str, Any]:
    if not os.path.exists(STATS_FILE):
        return {"users": [], "downloads": 0}
    try:
        with open(STATS_FILE) as f:
            data = json.load(f)
            # Ensure structure
            if "users" not in data:
                data["users"] = []
            if "downloads" not in data:
                data["downloads"] = 0
            return data
    except Exception as e:
        logger.error(f"Error loading stats: {e}")
        return {"users": [], "downloads": 0}


def _save_stats(data: dict[str, Any]):
    try:
        os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
        with open(STATS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving stats: {e}")


def record_activity(uid: int, activity_type: str = "download"):
    """
    Registra actividad.
    activity_type: 'download' (incrementa downloads y unique users)
                   'interaction' (solo unique users, si quisiéramos traquear solo uso)
    """
    data = _load_stats()

    # Update unique users
    if uid not in data["users"]:
        data["users"].append(uid)

    if activity_type == "download":
        data["downloads"] += 1

    _save_stats(data)


async def get_stats_summary(period: str = "day") -> dict[str, Any]:
    """
    Obtiene métricas del periodo solicitado consultando la BD Postgres.
    period: 'day', 'month', 'year', 'all'
    """
    from sqlalchemy import text

    from config.config_settings import config
    from core.db_manager_pg import pg_manager

    if not config.ENABLE_POSTGRES_PLUGIN:
        return {"unique_users": 0, "total_downloads": 0, "new_users": 0, "by_role": {}}

    try:
        # SQLite modifiers mapping to Postgres intervals
        intervals = {
            "day": "1 day",
            "month": "1 month",
            "year": "1 year"
        }
        
        async with pg_manager.get_session() as session:
            if period == "all":
                time_filter = "TRUE"
                user_time_filter = "TRUE"
            else:
                interval = intervals.get(period, "1 day")
                time_filter = f"downloaded_at >= NOW() - INTERVAL '{interval}'"
                user_time_filter = f"created_at >= NOW() - INTERVAL '{interval}'"

            # Total Downloads
            q_downloads = text(f"SELECT COUNT(*) FROM download_history WHERE {time_filter}")
            res_downloads = await session.execute(q_downloads)
            downloads = res_downloads.scalar() or 0

            # Unique Users (Downloaders)
            q_active = text(f"SELECT COUNT(DISTINCT user_id) FROM download_history WHERE {time_filter}")
            res_active = await session.execute(q_active)
            active_users = res_active.scalar() or 0

            # New Users joined
            q_new = text(f"SELECT COUNT(*) FROM users WHERE {user_time_filter}")
            res_new = await session.execute(q_new)
            new_users = res_new.scalar() or 0

            return {
                "unique_users": active_users,
                "total_downloads": downloads,
                "new_users": new_users,
                "by_role": {}
            }
    except Exception as e:
        logger.error(f"Error getting stats from Postgres: {e}")
        return {"unique_users": 0, "total_downloads": 0, "new_users": 0, "by_role": {}}


async def get_daily_stats() -> dict[str, Any]:
    """Compatibility wrapper for existing calls."""
    return await get_stats_summary("day")


def reset_stats():
    """Resetea las estadísticas diarias."""
    try:
        if os.path.exists(STATS_FILE):
            os.remove(STATS_FILE)
            logger.info("Estadísticas diarias reseteadas.")
    except Exception as e:
        logger.error(f"Error reseteando estadísticas: {e}")
