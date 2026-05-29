# handlers/commands/start_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.library_ui_service import mostrar_menu_principal
from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class StartHandler(BaseCommandHandler):
    """
    Handle /start command - User initialization and welcome.
    Single Responsibility: User onboarding and state management.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start: initialize state; admin->evil, others->normal."""
        uid = update.effective_user.id

        # Capture message_thread_id for topic support
        thread_id = get_thread_id(update)

        # API 9.3: Support for topics in private chat
        bot_user_dict = update.effective_user.to_dict()
        has_topics = bot_user_dict.get("has_topics_enabled", False)

        if has_topics:
            from services.topic_service import topic_service

            # Ensure topics exist and get "System" topic ID for welcome
            topic_ids = await topic_service.ensure_topics(context.bot, uid)
            if topic_ids:
                # If topics exist, redirect welcome message to "System" topic
                thread_id = topic_ids.get("sistema", thread_id)

        welcome_text = await self._get_welcome_text(update)
        await self._send_message(update, welcome_text, thread_id)

        # Clean previous temporary book state on restart
        self._clean_user_state(uid)

        await mostrar_menu_principal(update, context)

    async def _get_welcome_text(self, update: Update) -> str:
        """Generate personalized welcome message based on user level."""
        uid = update.effective_user.id
        user_info = await self._get_user_info(update)
        level = user_info.get("level", "free")
        role = user_info.get("role")
        is_admin = user_info.get("is_real_admin", False)
        is_publisher = level == "staff" and role == "Publicador"

        if is_admin and not is_publisher:
            return "🔧 <b>Modo Administrador</b>\n\nComandos especiales disponibles:\n• /evil - Modo mantenimiento\n• /changeweb - Cambiar interfaz\n\nUsa /catalog para continuar."

        text = "📚 <b>Bienvenido a ZeePub</b>\n\n"
        text += "Tu biblioteca personal de novelas ligeras.\n\n"
        text += "📖 <b>Comandos disponibles:</b>\n"
        text += "• /catalog - Explorar catálogo\n"
        text += "• /search - Buscar títulos\n"
        text += "• /status - Ver tu estado\n"
        text += "• /cancel - Cancelar operación\n"

        if is_publisher:
            text += "\n🎯 <b>Modo Publicador:</b>\n"
            text += "• /upload - Subir nuevo contenido\n"
            text += "• /bulk - Operaciones masivas\n"

        text += "\n💡 <b>Ayuda:</b>\n"
        text += "Escribe cualquier comando o usa /catalog para explorar."

        return text
