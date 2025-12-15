import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.config_settings import config
from repositories.user_repository import UserRepository
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)

# Singleton repository instance
user_repo = UserRepository()
# Cache for user info (5 minutes)
user_cache = AsyncTTLCache(ttl_seconds=300)


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
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def remove_user(telegram_id: int):
    await user_repo.delete(telegram_id)
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def update_user_status_label(telegram_id: int, new_label: str):
    await user_repo.update_status(telegram_id, new_label)
    await user_cache.invalidate(f"user_effective:{telegram_id}")


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
    # 0. Check Cache
    cache_key = f"user_effective:{uid}"
    cached = await user_cache.get(cache_key)
    if cached:
        return cached

    result = {"role": "free", "status_label": "Lector", "expires_at": None}

    # 1. Check DB (Async)
    info = await get_user_info(uid)
    if info:
        # Check expiration
        expires_at = info.get("expires_at")
        if expires_at and expires_at < datetime.now():
            # Expired
            result = {
                "role": "free",
                "status_label": "Expirado",
                "expires_at": expires_at,
            }
        else:
            role = info.get("role", "free").lower()
            custom_status = info.get("custom_status")

            # Normalize DB roles to internal standards just in case
            result = {
                "role": role,
                "status_label": custom_status or role.capitalize(),
                "expires_at": expires_at,
            }
    
    # 2. Legacy / Config Checks (if not found in DB or if DB says free but config says otherwise? 
    # Logic in v3.1.3 favored DB if present, but here we fallback if DB absent OR if we want to override?
    # Keeping original logic structure: if info found, we returned.
    # Wait, the original code had multiple returns. I must preserve PRECEDENCE.
    
    # Restoring original structure but capturing result for caching
    elif uid in config.ADMIN_USERS:
        result = {"role": "admin", "status_label": "Admin", "expires_at": None}

    elif uid in config.FACEBOOK_PUBLISHERS:
        result = {"role": "staff", "status_label": "Publisher", "expires_at": None}

    elif uid in config.PREMIUM_LIST:
        result = {
            "role": "premium",
            "status_label": "Premium (Legacy)",
            "expires_at": None,
        }

    elif uid in config.VIP_LIST:
        result = {"role": "vip", "status_label": "VIP (Legacy)", "expires_at": None}

    elif uid in config.WHITELIST:
        result = {
            "role": "white",
            "status_label": "Patrocinador (Legacy)",
            "expires_at": None,
        }
    
    # Save to cache
    await user_cache.set(cache_key, result)
    return result


async def get_users_by_role(role: str) -> list[Dict[str, Any]]:
    """
    Retorna lista de usuarios con un rol específico desde la DB.
    """
    return await user_repo.get_by_role(role)


# Init DB is handled by DatabaseManager/UserRepository instantiation
# We don't need init_user_db() explicit call here as repo handles connections lazily or via manager
