import logging
from typing import Annotated, Any

from fastapi import Cookie, Depends, Header, HTTPException, Query

from config.config_settings import config
from services.rbac_service import Permission
from services.user_service import get_effective_user, get_user_access_data
from utils.security import validate_telegram_data

logger = logging.getLogger(__name__)


async def get_telegram_user_id(
    authorization: Annotated[str | None, Header()] = None,
    cf_access_authenticated_user_email: Annotated[str | None, Header(alias="Cf-Access-Authenticated-User-Email")] = None,
    cf_access_user_email: Annotated[str | None, Header(alias="cf-access-authenticated-user-email")] = None,
    cf_access_jwt_assertion: Annotated[str | None, Header(alias="Cf-Access-Jwt-Assertion")] = None,
    x_telegram_init_data: Annotated[str | None, Header(alias="x-telegram-init-data")] = None,
    x_telegram_data: Annotated[str | None, Header(alias="X-Telegram-Data")] = None,
    tg_session: Annotated[str | None, Cookie()] = None,
    uid: Annotated[int | None, Query()] = None,
) -> int:
    """
    Dependency that extracts and validates the Telegram User ID from headers, cookies or query.
    Supports Cloudflare Access Email, Telegram OAuth Cookie, Telegram WebApp initData, and Supabase Auth.
    """
    # 0. Telegram OAuth Direct Session Cookie (Highest Priority for Web Authenticated via Telegram)
    if tg_session and str(tg_session).isdigit():
        return int(tg_session)

    # 0.1 Cloudflare Access Email Auth (Web Standalone)
    cf_email = (cf_access_authenticated_user_email or cf_access_user_email or "").strip().lower()

    if not cf_email and cf_access_jwt_assertion:
        try:
            import base64
            import json

            parts = cf_access_jwt_assertion.split(".")
            if len(parts) >= 2:
                payload_b64 = parts[1]
                payload_b64 += "=" * (-len(payload_b64) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                cf_email = (payload.get("email") or "").strip().lower()
        except Exception as e:
            logger.debug(f"Failed to parse Cloudflare JWT assertion: {e}")

    if cf_email:
        try:
            from services.user_service import get_or_create_user_by_email

            user_id = await get_or_create_user_by_email(cf_email)
            return user_id
        except Exception as e:
            logger.error(f"Cloudflare email DB lookup/creation failed: {e}")

    init_data = x_telegram_init_data or x_telegram_data
    bot_token = config.TELEGRAM_TOKEN

    # Local development bypass
    if init_data and "debug" in str(init_data).lower():
        # Return first admin from config if available, else a default
        admin_id = list(config.ADMIN_USERS)[0] if config.ADMIN_USERS else 133994080
        return admin_id

    # 1. Telegram WebApp Auth (Priority)
    if init_data:
        user_data = validate_telegram_data(init_data, bot_token)
        if not user_data:
            logger.warning(f"Invalid initData received: {init_data[:20]}...")
            # We don't raise here yet to allow Supabase fallback
        else:
            user_id = user_data.get("user", {}).get("id")
            if user_id:
                return user_id

    # 2. Supabase Auth (Fallback for Browser)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        from core.supabase_manager import supabase_manager

        if supabase_manager.is_active:
            try:
                # get_user validates the token with Supabase
                user_res = supabase_manager.get_client().auth.get_user(token)
                if user_res.user and user_res.user.email:
                    from services.user_service import get_user_by_email

                    db_user = await get_user_by_email(user_res.user.email)
                    if db_user:
                        return db_user.get("telegram_id", 0)
            except Exception as e:
                logger.debug(f"Supabase auth validation failed: {e}")

    # Fallback for dev or legacy (insecure)
    if uid:
        return uid

    # Anonymous or unauthorized
    return 0


async def get_current_user_data(
    user_id: Annotated[int, Depends(get_telegram_user_id)],
    authorization: Annotated[str | None, Header()] = None,
    x_telegram_init_data: Annotated[str | None, Header(alias="x-telegram-init-data")] = None,
    x_telegram_data: Annotated[str | None, Header(alias="X-Telegram-Data")] = None,
    x_simulated_level: Annotated[str | None, Header(alias="x-simulated-level")] = None,
) -> dict[str, Any]:
    """
    Dependency that returns the full effective user data (Profile + Permissions).
    Use this when you need UI settings or nickname.
    """
    if user_id == 0:
        return {
            "user_id": 0,
            "level": "anonymous",
            "role": None,
            "has_mini_app_access": False,
            "permissions": [],
        }

    # Extract user metadata from initData to allow nickname sync
    init_data = x_telegram_init_data or x_telegram_data
    tg_user = None
    if init_data and "debug" in str(init_data).lower():
        tg_user = {
            "id": user_id,
            "first_name": "Admin (Debug)",
            "username": "admin_debug",
        }
    elif init_data:
        try:
            res = validate_telegram_data(init_data, config.TELEGRAM_TOKEN)
            if res:
                tg_user = res.get("user")
        except Exception:
            pass

    # If simulated level is provided, convert to int
    sim_level = None
    if x_simulated_level and x_simulated_level.isdigit():
        sim_level = int(x_simulated_level)

    data = await get_effective_user(user_id, tg_user=tg_user, simulated_level_id=sim_level)

    # Override level to admin for debug mode
    if init_data and "debug" in str(init_data).lower():
        data["level"] = "admin"
        data["is_real_admin"] = True
        data["permissions"] = ["all"]

    data["user_id"] = user_id
    data["telegram_id"] = user_id
    return data


async def get_current_user_permissions(
    user_id: Annotated[int, Depends(get_telegram_user_id)],
) -> dict[str, Any]:
    """
    Lighter dependency that ONLY returns access data (Tier + Permissions).
    Faster than get_current_user_data as it skips UI/Theme loading.
    """
    return await get_user_access_data(user_id)


async def require_admin(
    access_data: Annotated[dict[str, Any], Depends(get_current_user_permissions)],
):
    """
    Enforces staff or higher roles.
    Uses the lighter access_data dependency.
    """
    if not access_data.get("isStaff") and not access_data.get("isAdmin"):
        raise HTTPException(status_code=403, detail="Admin or Staff privileges required")
    return access_data


async def require_mini_app_access(
    access_data: Annotated[dict[str, Any], Depends(get_current_user_permissions)],
):
    """
    Enforces mini app access permission.
    """
    # Admins/Staff always have access, others check granular permission
    if not access_data.get("isStaff") and Permission.ACCESS_MINI_APP.value not in access_data.get("permissions", []):
        raise HTTPException(
            status_code=403,
            detail="⛔ El acceso a la Mini App está restringido actualmente.",
        )
    return access_data
