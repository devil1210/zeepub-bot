import logging
from typing import Any

from api.handlers.helpers import check_staff
from services.theme_service import theme_service
from services.theme_sync_service import theme_sync_service

logger = logging.getLogger(__name__)

async def handle_admin_get_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Retorna la lista de plantillas de temas disponibles."""
    try:
        themes = await theme_service.get_all_themes()
        logger.info(f"Returning {len(themes)} themes to frontend")
        return {"success": True, "themes": themes}
    except Exception as e:
        logger.error(f"Error fetching themes: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_sync_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Ejecuta sincronización manual de temas."""
    check_staff(user_data)
    try:
        result = await theme_sync_service.manual_sync()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in manual theme sync: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_rename_themes(data: dict[str, Any], user_data: dict[str, Any]):
    """Renombra temas duplicados con nombres únicos usando detección mejorada."""
    check_staff(user_data)
    try:
        results = await theme_service.fix_duplicate_names()
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Error renaming themes: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_get_theme_sync_logs(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene historial de sincronizaciones de temas."""
    check_staff(user_data)
    try:
        logs = await theme_sync_service.get_sync_logs(limit=data.get("limit", 50))
        return {"success": True, "logs": logs}
    except Exception as e:
        logger.error(f"Error fetching theme sync logs: {e}")
        return {"success": False, "message": str(e)}

async def handle_admin_save_theme(data: dict[str, Any], user_data: dict[str, Any]):
    """Guarda o actualiza un tema."""
    check_staff(user_data)
    try:
        theme = await theme_service.save_theme(data)
        return {"success": True, "theme": theme}
    except Exception as e:
        logger.error(f"Error saving theme: {e}")
        return {"success": False, "message": str(e)}
