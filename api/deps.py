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
    bot_token = config.TELEGRAM_TOKEN

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
    user_id: int = Depends(get_telegram_user_id),
) -> Dict[str, Any]:
    """
    Dependency that returns the full effective user data.
    """
    if user_id == 0:
        return {"user_id": 0, "role": "anonymous", "has_mini_app_access": False}

    # Extract user metadata from initData to allow nickname sync
    init_data = x_telegram_init_data or x_telegram_data
    tg_user = None
    if init_data:
        try:
            res = validate_telegram_data(init_data, config.TELEGRAM_TOKEN)
            if res:
                tg_user = res.get("user")
        except Exception:
            pass

    data = await get_effective_user(user_id, tg_user=tg_user)
    data["user_id"] = user_id
    data["telegram_id"] = user_id
    return data


async def require_admin(user_data: Dict[str, Any] = Depends(get_current_user_data)):
    """
    Dependency that enforces admin role.
    """
    if user_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user_data


async def require_mini_app_access(
    user_data: Dict[str, Any] = Depends(get_current_user_data)
):
    """
    Dependency that enforces Mini App access permissions.
    """
    if not user_data.get("has_mini_app_access") and user_data.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="⛔ El acceso a la Mini App está restringido actualmente.",
        )
    return user_data
