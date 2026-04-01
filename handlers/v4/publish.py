import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.v4.base import BaseHandlerV4, with_services

logger = logging.getLogger(__name__)


class PublishHandlerV4(BaseHandlerV4):
    """
    Manejador para el inicio del proceso de publicación v4.0.
    """

    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Maneja el comando /upload para publicadores."""
        user_id = update.effective_user.id

        # Check permissions using services
        user_service = services.get("user_service")
        user_info = await user_service.get_effective_user(user_id)
        role = user_info.get("role", "free")
        level = user_info.get("level", "free")

        is_admin = role == "admin"
        is_publisher = level == "staff" and role == "Publicador"

        if not (is_admin or is_publisher):
            await update.message.reply_text("🚫 No tienes permisos para usar este comando.")
            return

        # Show instructions to use the miniapp
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

        from config.config_settings import config

        webapp_url = config.WEBAPP_URL + "/publish"
        keyboard = [[InlineKeyboardButton("📤 Abrir Panel de Publicación", web_app=WebAppInfo(url=webapp_url))]]
        markup = InlineKeyboardMarkup(keyboard)

        text = (
            "🚀 <b>Modo Publicación Iniciado</b>\n\n"
            "Usa la MiniApp para subir y procesar nuevos libros.\n"
            "El panel te guiará paso a paso para añadir metadatos, seleccionar portada y generar el EPUB."
        )

        await update.message.reply_text(text, reply_markup=markup, parse_mode="HTML")
