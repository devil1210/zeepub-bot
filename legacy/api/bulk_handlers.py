"""
Handlers para operaciones masivas de librería
"""

import logging
from typing import Any

from services.bulk_review_service import bulk_review_service

logger = logging.getLogger(__name__)


async def handle_bulk_analyze_library(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """
    Maneja el análisis masivo de la librería
    """
    try:
        filters = data.get("filters", {})
        batch_size = data.get("batch_size", 100)

        result = await bulk_review_service.analyze_library(filters, batch_size)
        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error en análisis masivo: {e}")
        return {"success": False, "error": str(e)}


async def handle_bulk_update_metadata(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """
    Maneja la actualización masiva de metadatos
    """
    try:
        updates = data.get("updates", [])
        if not updates:
            return {"success": False, "error": "No updates provided"}

        result = await bulk_review_service.bulk_update_metadata(updates)
        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error en actualización masiva: {e}")
        return {"success": False, "error": str(e)}


async def handle_bulk_get_job_status(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """
    Maneja la obtención del estado de un trabajo masivo
    """
    try:
        job_id = data.get("job_id")
        if not job_id:
            return {"success": False, "error": "Job ID required"}

        status = await bulk_review_service.get_job_status(job_id)
        return {"success": True, "status": status}

    except Exception as e:
        logger.error(f"Error obteniendo estado del job: {e}")
        return {"success": False, "error": str(e)}
