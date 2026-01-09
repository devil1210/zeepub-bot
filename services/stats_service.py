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


async def get_stats_summary(period: str = "day") -> Dict[str, Any]:
    """
    Obtiene métricas del periodo solicitado consultando la BD real via db_manager.
    period: 'day', 'month', 'year', 'all'
    """
    from core.db_manager import db_manager
    
    # Obtener conteos crudos (Descargas, Usuarios Activos, Nuevos Usuarios)
    counts = await db_manager.get_stats_counts(period)
    
    # Para consistencia con el plugin anterior, mapeamos las keys
    return {
        "unique_users": counts["active_users"],
        "total_downloads": counts["downloads"],
        "new_users": counts["new_users"],
        "by_role": {} # TODO: Implementar desglose por rol si es crítico, pero para rendimiento es mejor omitir en queries masivos
    }

async def get_daily_stats() -> Dict[str, Any]:
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
