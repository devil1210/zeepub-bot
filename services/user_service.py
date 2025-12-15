import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.config_settings import config
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Singleton repository instance
user_repo = UserRepository()


async def upsert_user(
    telegram_id: int,
    role: str,
    duration_months: Optional[int] = None,
    custom_status: Optional[str] = None,
    created_by: Optional[int] = None,
    duration_days: Optional[int] = None,
):
    """
    Agrega o actualiza un usuario.
    Si duration_months/days es None y no existe, es 'infinito'.
    """
    expires_at = None
    from datetime import timedelta

    now = datetime.now()

    if duration_days is not None:
        expires_at = now + timedelta(days=duration_days)
    elif duration_months is not None:
        # Simple approximation: 30 days * months
        days = duration_months * 30
        expires_at = now + timedelta(days=days)

    await user_repo.upsert(telegram_id, role, expires_at, custom_status, created_by)


async def remove_user(telegram_id: int):
    await user_repo.delete(telegram_id)


async def update_user_status_label(telegram_id: int, new_label: str):
    await user_repo.update_status(telegram_id, new_label)


async def get_user_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Retorna info del usuario desde DB.
    """
    return await user_repo.get_by_id(telegram_id)


async def get_effective_user(uid: int) -> Dict[str, Any]:
    """
    Determina el rol efectivo del usuario y estado, considerando DB y Config (legacy).
    Retorna un dict con keys: role, status_label, expires_at (puede ser None).
    Roles: 'admin', 'staff', 'premium', 'vip', 'white', 'free'.
    """
    # 1. Check DB (Async)
    info = await get_user_info(uid)
    if info:
        # Check expiration
        expires_at = info.get("expires_at")
        if expires_at and expires_at < datetime.now():
            # Expired
            return {
                "role": "free",
                "status_label": "Expirado",
                "expires_at": expires_at,
            }

        role = info.get("role", "free").lower()
        custom_status = info.get("custom_status")

        # Normalize DB roles to internal standards just in case
        return {
            "role": role,
            "status_label": custom_status or role.capitalize(),
            "expires_at": expires_at,
        }

    # 2. Legacy / Config Checks
    if uid in config.ADMIN_USERS:
        return {"role": "admin", "status_label": "Admin", "expires_at": None}

    if uid in config.FACEBOOK_PUBLISHERS:
        return {"role": "staff", "status_label": "Publisher", "expires_at": None}

    if uid in config.PREMIUM_LIST:
        return {
            "role": "premium",
            "status_label": "Premium (Legacy)",
            "expires_at": None,
        }

    if uid in config.VIP_LIST:
        return {"role": "vip", "status_label": "VIP (Legacy)", "expires_at": None}

    if uid in config.WHITELIST:
        return {
            "role": "white",
            "status_label": "Patrocinador (Legacy)",
            "expires_at": None,
        }

    return {"role": "free", "status_label": "Lector", "expires_at": None}


async def get_users_by_role(role: str) -> list[Dict[str, Any]]:
    """
    Retorna lista de usuarios con un rol específico desde la DB.
    """
    return await user_repo.get_by_role(role)


# Init DB is handled by DatabaseManager/UserRepository instantiation
# We don't need init_user_db() explicit call here as repo handles connections lazily or via manager
