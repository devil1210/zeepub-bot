from fastapi import Header, HTTPException, Query, Depends
from typing import Optional, Dict, Any
import logging
from config.config_settings import config
from utils.security import validate_telegram_data
from services.user_service import get_effective_user

logger = logging.getLogger(__name__)


async def get_telegram_user_id(
    x_telegram_init_data: Optional[str] = Header(None, alias="x-telegram-init-data"),
    x_telegram_data: Optional[str] = Header(None, alias="X-Telegram-Data"),
    uid: Optional[int] = Query(None),
) -> int:
    """
    Dependency that extracts and validates the Telegram User ID from headers or query.
    Prioritizes initData validation for security.
    """
    init_data = x_telegram_init_data or x_telegram_data
    logger.debug(f"Received init_data='{init_data}' (type: {type(init_data)})")
    bot_token = config.TELEGRAM_TOKEN

    # Local development bypass
    if init_data and "debug" in str(init_data).lower():
        # Return first admin from config if available, else a default
        admin_id = list(config.ADMIN_USERS)[0] if config.ADMIN_USERS else 133994080
        return admin_id

    if init_data:
        user_data = validate_telegram_data(init_data, bot_token)
        if not user_data:
            logger.warning(f"Invalid initData received: {init_data[:20]}...")
            raise HTTPException(status_code=401, detail="Invalid Telegram data")

        user_id = user_data.get("user", {}).get("id")
        if user_id:
            return user_id

    # Fallback for dev or legacy (insecure)
    if uid:
        return uid

    # Anonymous or unauthorized
    return 0


async def get_current_user_data(
    x_telegram_init_data: Optional[str] = Header(None, alias="x-telegram-init-data"),
    x_telegram_data: Optional[str] = Header(None, alias="X-Telegram-Data"),
    x_simulated_level: Optional[str] = Header(None, alias="x-simulated-level"),
    user_id: int = Depends(get_telegram_user_id),
) -> Dict[str, Any]:

    """
    Dependency that returns the full effective user data.
    """
    if user_id == 0:
        return {"user_id": 0, "level": "anonymous", "role": None, "has_mini_app_access": False}

    # Extract user metadata from initData to allow nickname sync
    init_data = x_telegram_init_data or x_telegram_data
    tg_user = None
    if init_data and "debug" in str(init_data).lower():
        tg_user = {"id": user_id, "first_name": "Admin (Debug)", "username": "admin_debug"}
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

    data["user_id"] = user_id
    data["telegram_id"] = user_id
    return data


async def require_admin(user_data: Dict[str, Any] = Depends(get_current_user_data)):
    """
    Dependency that enforces admin role.
    Allows real admins even if they are currently simulating another level.
    """
    if user_data.get("level") != "admin" and not user_data.get("is_real_admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user_data


async def require_mini_app_access(
    user_data: Dict[str, Any] = Depends(get_current_user_data)
):
    curr_uid = user_data.get("user_id", 0)
    is_configured_admin = curr_uid in config.ADMIN_USERS
    if not user_data.get("has_mini_app_access") and user_data.get("level") != "admin" and not user_data.get("is_real_admin") and not is_configured_admin:
        raise HTTPException(
            status_code=403,
            detail="⛔ El acceso a la Mini App está restringido actualmente.",
        )
    return user_data
