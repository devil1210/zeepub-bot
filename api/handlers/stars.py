import logging
from typing import Any
from fastapi import HTTPException

from api.main import bot

logger = logging.getLogger(__name__)


async def handle_create_stars_invoice(data: dict[str, Any], user_data: dict[str, Any]):
    """Crea un link de factura de Telegram Stars."""
    tier = data.get("tier", "premium")
    amount = data.get("amount", 100)

    stars_plugin = bot.plugin_manager.get_plugin("stars_payment")
    cms_plugin = bot.plugin_manager.get_plugin("custom_messages")
    if not stars_plugin:
        raise HTTPException(status_code=500, detail="Stars Payment Plugin not found")

    # Implementation will be moved from api/miniapp_handlers.py
    pass
