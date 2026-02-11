import logging
from typing import Any

from fastapi import HTTPException
from services.rbac_service import rbac_service

logger = logging.getLogger(__name__)


def check_admin(user_data: dict[str, Any]):
    """Checks if the user has Admin privileges."""
    uid = user_data.get("user_id") or user_data.get("telegram_id")
    if not rbac_service.is_admin(user_data):
        logger.warning(f"Admin Access Denied for user {uid} (Level: {user_data.get('level')})")
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado: Se requieren permisos de Administrador",
        )


def check_staff(user_data: dict[str, Any]):
    """Checks if the user has Staff or Admin privileges."""
    uid = user_data.get("user_id") or user_data.get("telegram_id")
    if not rbac_service.is_staff(user_data):
        logger.warning(f"Staff Access Denied for user {uid} (Level: {user_data.get('level')})")
        raise HTTPException(
            status_code=403,
            detail=f"Acceso denegado: Se requieren permisos de Staff (Tu nivel: {user_data.get('level')})",
        )
    logger.info(f"Staff access verified for user {uid}")
