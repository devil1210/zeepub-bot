import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from config.config_settings import config
from repositories.user_repository import UserRepository
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)

# Singleton repository instance
user_repo = UserRepository()
# Cache for user info (1 hour) - changed from 5 minutes for high-volume bot (1000+ msg/sec)
user_cache = AsyncTTLCache(ttl_seconds=3600)


async def upsert_user(
    telegram_id: int,
    role: str,
    duration_months: Optional[int] = None,
    custom_status: Optional[str] = None,
    created_by: Optional[int] = None,
    duration_days: Optional[int] = None,
    nickname: Optional[str] = None,
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

    await user_repo.upsert(
        telegram_id, role, expires_at, custom_status, created_by, nickname
    )
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def remove_user(telegram_id: int):
    await user_repo.delete(telegram_id)
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def update_user_status_label(telegram_id: int, new_label: Optional[str]):
    # Check if user exists first
    info = await get_user_info(telegram_id)
    if not info:
        # User not in DB, retrieve effective role (e.g. from config) and upsert
        eff = await get_effective_user(telegram_id)
        role = eff.get("role", "free")
        # Upsert with new label
        await upsert_user(telegram_id, role=role, custom_status=new_label)
    else:
        # Just update
        await user_repo.update_status(telegram_id, new_label)

    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def update_user_nickname(telegram_id: int, new_nickname: Optional[str]):
    # Check if user exists first
    info = await get_user_info(telegram_id)
    if not info:
        # User not in DB, retrieve effective role and upsert
        eff = await get_effective_user(telegram_id)
        role = eff.get("role", "free")
        # Upsert with new nickname
        await upsert_user(telegram_id, role=role, nickname=new_nickname)
    else:
        await user_repo.update_nickname(telegram_id, new_nickname)

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

    result = {
        "role": "free",
        "status_label": "Lector",
        "expires_at": None,
        "nickname": None,
    }

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
                "nickname": info.get("nickname"),
            }
        else:
            role = info.get("role", "free").lower()
            custom_status = info.get("custom_status")

            # Normalize DB roles to internal standards just in case
            result = {
                "role": role,
                "status_label": custom_status or role.capitalize(),
                "expires_at": expires_at,
                "nickname": info.get("nickname"),
                "custom_status": custom_status,
            }

    # 1.1 Check Level and Admin status (New system)
    access_info = await user_repo.get_access_info(uid)
    if access_info:
        result["has_mini_app_access"] = access_info["hasAccess"]
        result["is_admin_db"] = access_info["isAdmin"]
        result["level_info"] = access_info["level"]
        # Priority: level name as status label if no custom status
        if not info or not info.get("custom_status"):
            result["status_label"] = access_info["level"]["name"]
        
        # Admin override
        if access_info["isAdmin"]:
            result["role"] = "admin"
            result["has_mini_app_access"] = True

    # 2. Legacy / Config Checks (if not found in DB or if DB says free but config says otherwise?
    # Logic in v3.1.3 favored DB if present, but here we fallback if DB absent OR if we want to override?
    # Keeping original logic structure: if info found, we returned.
    # Wait, the original code had multiple returns. I must preserve PRECEDENCE.

    # Restoring original structure but capturing result for caching
    elif uid in config.ADMIN_USERS:
        result = {
            "role": "admin",
            "status_label": "Admin",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.FACEBOOK_PUBLISHERS:
        result = {
            "role": "staff",
            "status_label": "Publisher",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.PREMIUM_LIST:
        result = {
            "role": "premium",
            "status_label": "Premium (Legacy)",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.VIP_LIST:
        result = {
            "role": "vip",
            "status_label": "VIP (Legacy)",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    elif uid in config.WHITELIST:
        result = {
            "role": "white",
            "status_label": "Patrocinador (Legacy)",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }

    # Save to cache
    await user_cache.set(cache_key, result)
    return result


async def get_users_by_role(role: str) -> list[Dict[str, Any]]:
    """
    Retorna lista de usuarios con un rol específico desde la DB.
    """
    return await user_repo.get_by_role(role)


async def upgrade_user_level(telegram_id: int, new_level_name: str):
    """
    Actualiza el nivel de un usuario buscando por nombre de nivel.
    """
    async with user_repo.db.connection() as conn:
        await conn.execute(
            """
            UPDATE users
            SET level_id = (SELECT id FROM user_levels WHERE name = ?)
            WHERE telegram_id = ?
            """,
            (new_level_name, telegram_id)
        )
        await conn.commit()
    await user_cache.invalidate(f"user_effective:{telegram_id}")


# Init DB is handled by DatabaseManager/UserRepository instantiation
# We don't need init_user_db() explicit call here as repo handles connections lazily or via manager
