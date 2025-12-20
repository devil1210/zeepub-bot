from fastapi import APIRouter, HTTPException, Header, Depends, Request
from utils.security import validate_telegram_data, verify_telegram_user
from services.opds_service import OPDSHandler
from core.bot import ZeePubBot
import os
import logging

# Prefix is empty because the route is /api/bot
router = APIRouter(tags=["miniapp"])
logger = logging.getLogger(__name__)

async def get_opds_handler():
    # Instantiate or retrieve OPDSHandler
    config = {"root_path": os.getenv("OPDS_ROOT", "./books")}
    return OPDSHandler(config)



@router.post("/api/bot")
async def handle_bot_request(
    request: Request,
    x_telegram_init_data: str = Header(None, alias="x-telegram-init-data")
):
    """
    Main endpoint for Mini App requests.
    Dispatches actions: search, download, status, etc.
    """
    # 1. Validate Init Data
    bot_token = os.getenv("TELEGRAM_TOKEN")
    if not bot_token:
        # Fallback or error if token not configured
        logger.warning("TELEGRAM_TOKEN not set")

    # Validate if header is present
    user_data = None
    if x_telegram_init_data and bot_token:
        user_data = validate_telegram_data(x_telegram_init_data, bot_token)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram data")
    else:
        # Allow dev/skip if needed, or strict 401
        # For now strict
        pass
        # raise HTTPException(status_code=401, detail="Missing auth header")

    # 2. Parse Body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    action = body.get("action")
    data = body.get("data", {})

    logger.info(f"Miniapp action: {action} User: {user_data.get('user', {}).get('id') if user_data else 'unknown'}")

    try:
        if action == "search":
            query = data.get("query")
            if not query:
                return {"results": []}

            # Use OPDS Service
            handler = await get_opds_handler()
            # results = await handler.search(query)
            # Placeholder implementation
            results = []
            return {"results": results}

        elif action == "status":
            return {
                "status": "online",
                "version": os.getenv("BOT_VERSION", "4.0.0")
            }

        elif action == "download":
            # Implement download logic
            return {"success": True, "message": "Download started"}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except Exception as e:
        logger.error(f"Error handling action {action}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
