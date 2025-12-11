import json
import os
import logging
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)

STATS_FILE = os.path.join("data", "daily_stats.json")


def _load_stats() -> Dict[str, Any]:
    if not os.path.exists(STATS_FILE):
        return {"users": [], "downloads": 0}
    try:
        with open(STATS_FILE, "r") as f:
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


def _save_stats(data: Dict[str, Any]):
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


def get_daily_stats() -> Dict[str, Any]:
    data = _load_stats()

    unique_users = data["users"]
    total_downloads = data["downloads"]

    # Calculate breakdown by role
    by_role = {}
    if unique_users:
        # Avoid circular import at top level if possible, or handle inside function
        from services.user_service import get_effective_user

        for uid in unique_users:
            try:
                user_info = get_effective_user(uid)
                role = user_info.get("role", "free")
                by_role[role] = by_role.get(role, 0) + 1
            except Exception as e:
                logger.error(f"Error getting effective user for stats {uid}: {e}")

    return {
        "unique_users": len(unique_users),
        "total_downloads": total_downloads,
        "by_role": by_role
    }


def reset_stats():
    """Resetea las estadísticas diarias."""
    try:
        if os.path.exists(STATS_FILE):
            os.remove(STATS_FILE)
            logger.info("Estadísticas diarias reseteadas.")
    except Exception as e:
        logger.error(f"Error reseteando estadísticas: {e}")
