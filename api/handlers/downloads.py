import logging
from typing import Any
from datetime import datetime

from fastapi import HTTPException
from api.handlers.helpers import check_staff, check_admin
from config.config_settings import config
from repositories.download_repository import download_repo
from services.delivery.delivery_service import delivery_service
from services.metadata_orchestrator.metadata_service import metadata_orchestrator
from services.notion_service import notion_service

logger = logging.getLogger(__name__)


async def handle_user_downloads_history(data: dict[str, Any], user_data: dict[str, Any]):
    """Devuelve el historial reciente de descargas del usuario."""
    user_id = user_data.get("user_id")
    try:
        downloads = await download_repo.get_user_downloads(user_id, limit=20)
        return {"downloads": downloads}
    except Exception as e:
        logger.error(f"Error fetching download history for user {user_id}: {e}")
        return {"downloads": []}


async def handle_download(data: dict[str, Any], user_data: dict[str, Any]):
    """Envía el archivo del libro directamente a través del bot."""
    # Implementation will be moved from api/miniapp_handlers.py
    pass
