import logging
from typing import Optional, Dict, Any
from datetime import datetime
from config.config_settings import config
from repositories.user_repository import user_repo
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)

# Cache for user info (5 minutes)
user_cache = AsyncTTLCache(ttl_seconds=300)


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


async def update_user_status_label(telegram_id: int, new_label: Optional[str]) -> None:
    # Check if user exists first
    info = await get_user_info(telegram_id)
    if not info:
        # User not in DB, retrieve effective role (e.g. from config) and upsert
        eff = await get_effective_user(telegram_id)
        role = eff.get("role", "free")
        # Upsert with new label
        await upsert_user(telegram_id, role=str(role), custom_status=new_label)
    else:
        # Just update
        await user_repo.update_status(telegram_id, new_label)

    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def update_user_nickname(telegram_id: int, new_nickname: Optional[str]) -> None:
    # Check if user exists first
    info = await get_user_info(telegram_id)
    if not info:
        # User not in DB, retrieve effective role and upsert
        eff = await get_effective_user(telegram_id)
        role = eff.get("role", "free")
        # Upsert with new nickname
        await upsert_user(telegram_id, role=str(role), nickname=new_nickname)
    else:
        await user_repo.update_nickname(telegram_id, new_nickname)

    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def get_user_info(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Retorna info del usuario desde DB.
    """
    return await user_repo.get_by_id(telegram_id)


async def get_effective_user(uid: int, use_cache: bool = True) -> Dict[str, Any]:
    """
    Determina el rol efectivo del usuario y estado, considerando DB y Config (legacy).
    Retorna un dict con keys: role, status_label, expires_at (puede ser None).
    Roles: 'admin', 'staff', 'premium', 'vip', 'white', 'free'.
    """
    # 0. Check Cache
    cache_key = f"user_effective:{uid}"
    if use_cache:
        cached = await user_cache.get(cache_key)
        if cached:
            return cached

    result = {
        "role": "free",
        "status_label": "Lector",
        "expires_at": None,
        "nickname": None,
    }

    # 1. Config Admins always have top precedence
    if uid in config.ADMIN_USERS:
        result = {
            "role": "admin",
            "status_label": "Admin",
            "expires_at": None,
            "nickname": None,
            "has_mini_app_access": True,
        }
        await user_cache.set(cache_key, result)
        return result

    # 2. Check DB (Async)
    info: Optional[Dict[str, Any]] = await get_user_info(uid)
    if info:
        # Check expiration
        expires_at: Optional[datetime] = info.get("expires_at")
        if expires_at and expires_at < datetime.now():
            # Expired
            result = {
                "role": "free",
                "status_label": "Expirado",
                "expires_at": expires_at,
                "nickname": info.get("nickname"),
                "custom_status": None,
                "has_mini_app_access": False,
            }
        else:
            role_db = info.get("role", "free")
            role_str = role_db.lower() if isinstance(role_db, str) else "free"
            custom_status = info.get("custom_status")

            # Normalize DB roles to internal standards just in case
            result = {
                "role": role_str,
                "status_label": custom_status or role_str.capitalize(),
                "expires_at": expires_at,
                "nickname": info.get("nickname"),
                "custom_status": custom_status,
                "custom_status": custom_status,
                "settings": info.get("settings", {}),
                # has_mini_app_access will be set by default logic below
            }

    # 4. Fallback default policy for non-DB users
    if not info and uid not in config.ADMIN_USERS:
        # PROACTIVE SYNC: Create minimal user record if not exists
        logger.info(f"Auto-registering user {uid} (Lector level)")
        await user_repo.create_minimal_user(uid)
        # Re-fetch access info to ensure result is populated
        access_info = await user_repo.get_access_info(uid)

    if "has_mini_app_access" not in result:
        # Default policy: Restricted access for unknown users (matching Lector behavior)
        # Admins and Staff from config will have this set to True explicitly below/above
        result["has_mini_app_access"] = False

    access_info = await user_repo.get_access_info(uid)
    if access_info:
        result["has_mini_app_access"] = access_info["hasAccess"]
        result["is_admin_db"] = access_info["isAdmin"]
        result["level_info"] = access_info["level"]

        # Override role with level name for consistent UI settings
        level_name = access_info["level"]["name"].lower()
        if level_name == "administrador":
            result["role"] = "admin"
        elif level_name == "lector":
            result["role"] = "free"
        elif level_name == "patrocinador":
            result["role"] = "white"  # Legacy mapping for whitelist
        else:
            result["role"] = level_name

        # Priority: level name as status label if no custom status
        if not info or not info.get("custom_status"):
            result["status_label"] = access_info["level"]["name"]

        # Admin override from DB (hardcoded check)
        if access_info["isAdmin"]:
            result["role"] = "admin"
            result["has_mini_app_access"] = True

    # 4. Legacy Config Fallbacks (non-admins)
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


async def upgrade_user_level(telegram_id: int, new_level_name: str) -> None:
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
            (new_level_name, telegram_id),
        )
        await conn.commit()
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def increment_download_count(telegram_id: int) -> int:
    """Incrementa el contador de descargas y retorna el nuevo total."""
    count = await user_repo.increment_download_count(telegram_id)
    return count


async def check_milestones(uid: int, context) -> Optional[str]:
    """Verifica si el usuario alcanzó un hito y retorna el mensaje de recompensa."""
    # This would ideally use templates from the custom_messages plugin
    user_info = await get_user_info(uid)
    if not user_info:
        return None

    count = user_info.get("total_downloads", 0)

    milestones = {
        10: "milestone_10_downloads",
        50: "milestone_50_downloads",
        100: "milestone_100_downloads",
    }

    if count in milestones:
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        slug = milestones[count]

        # Default messages if plugin not active or template not set
        defaults = {
            10: "🎁 ¡Felicidades! Has descargado tus primeros 10 libros. 🎉",
            50: "🌟 ¡Increíble! Ya llevas 50 libros descargados. Eres un lector apasionado. 📚",
            100: "👑 ¡Master Lector! 100 libros descargados. ¡Tu biblioteca es legendaria! 🏆",
        }

        if cms and cms.enabled:
            return await cms.get_text(
                slug, user=None
            )  # user will be handled by plugin if needed
        return defaults.get(count)

    return None


async def invalidate_user_cache(telegram_id: int):
    """Limpia la caché de un usuario específico."""
    await user_cache.invalidate(f"user_effective:{telegram_id}")


async def get_user_settings(telegram_id: int) -> Dict[str, Any]:
    """Obtiene la configuración personal del usuario."""
    info = await get_user_info(telegram_id)
    if info:
        return info.get("settings", {})
    return {}


async def update_user_setting(telegram_id: int, key: str, value: Any) -> Dict[str, Any]:
    """Actualiza una clave específica de la configuración del usuario."""
    current_settings = await get_user_settings(telegram_id)
    current_settings[key] = value

    # Ensure user exists (if not, upsert first)
    info = await get_user_info(telegram_id)
    if not info:
        eff = await get_effective_user(telegram_id)
        await upsert_user(telegram_id, role=str(eff.get("role", "free")))

    await user_repo.update_user_settings(telegram_id, current_settings)
    await user_cache.invalidate(f"user_effective:{telegram_id}")
    return current_settings


# Init DB is handled by DatabaseManager/UserRepository instantiation
# We don't need init_user_db() explicit call here as repo handles connections lazily or via manager
