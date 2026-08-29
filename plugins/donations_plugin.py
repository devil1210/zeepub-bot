import logging
import os

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from services.library_ui import build_donations_rich_blocks
from services.rich_message_service import RichMessageService
from services.settings_service import get_setting
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class DonationsPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "donations"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Sistema de donaciones, membresías VIP/Premium y beneficios."

    def __init__(self):
        super().__init__()
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_DONATIONS", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin Donations desactivado por configuración.")
            return False

        try:
            app = bot_instance
            app.add_handler(CommandHandler(["donar", "donate", "niveles", "levels"], self.donate))
            logger.info("Plugin Donations: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Donations: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def donate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donar y /niveles: envía ficha interactiva con beneficios y enlaces de donación."""
        thread_id = get_thread_id(update)
        user_name = update.effective_user.first_name or "Lector"
        uid = update.effective_user.id

        p_white = get_setting("price_whitelist", "5")
        p_vip = get_setting("price_vip", "10")
        p_premium = get_setting("price_premium", "20")
        months = get_setting("benefit_duration_months", "6")

        donation_url = getattr(config, "DONATION_URL", "https://ko-fi.com/zeepubs")

        blocks = build_donations_rich_blocks(
            user_name=user_name,
            donation_url=donation_url,
            p_white=p_white,
            p_vip=p_vip,
            p_premium=p_premium,
            duration_months=months,
        )

        rich_kwargs = {}
        es_grupo = update.effective_chat and update.effective_chat.type in ("group", "supergroup")
        if es_grupo:
            rich_kwargs["receiver_user_id"] = uid

        res = await RichMessageService.send_rich_message(
            chat_id=update.effective_chat.id,
            blocks=blocks,
            message_thread_id=thread_id,
            **rich_kwargs,
        )

        if not res or not res.get("ok"):
            fallback_text = (
                f"☕ <b>Membresías y Donaciones • ZeePubs</b>\n\n"
                f"Hola <b>{user_name}</b>, gracias por apoyar nuestro proyecto.\n\n"
                f"• 🤍 <b>Whitelist (${p_white} USD):</b> 10 descargas/día\n"
                f"• ⭐ <b>VIP (${p_vip} USD):</b> Descargas Ilimitadas\n"
                f"• 💎 <b>Premium (${p_premium} USD):</b> Ilimitadas + Prioridad\n\n"
                f"👉 <a href='{donation_url}'>Donar en Ko-fi</a>"
            )
            api_kwargs = {"receiver_user_id": uid} if es_grupo else None
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=fallback_text,
                parse_mode="HTML",
                message_thread_id=thread_id,
                api_kwargs=api_kwargs,
            )

