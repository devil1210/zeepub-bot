import logging
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def handle_create_stars_invoice(data: dict[str, Any], user_data: dict[str, Any]):
    """Crea un link de factura de Telegram Stars."""
    tier = data.get("tier", "premium")
    amount = data.get("amount", 100)
    from api.main import bot

    stars_plugin = bot.plugin_manager.get_plugin("stars_payment")
    cms_plugin = bot.plugin_manager.get_plugin("custom_messages")
    if not stars_plugin:
        raise HTTPException(status_code=500, detail="Stars Payment Plugin not found")

    title = f"Nivel {tier.capitalize()}"
    desc = f"Suscripción al nivel {tier.capitalize()}"
    if cms_plugin:
        desc = await cms_plugin.get_text("star_payment_invoice_desc", Nivel=tier.capitalize())

    invoice_link = await stars_plugin.create_stars_invoice_link(
        title=title, description=desc, payload=f"upgrade_{tier}", amount=amount
    )
    return {"invoiceLink": invoice_link}
