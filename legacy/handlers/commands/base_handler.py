# handlers/commands/base_handler.py

import logging
from abc import ABC, abstractmethod

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class BaseCommandHandler(ABC):
    """
    Base class for all command handlers with common functionality.
    Implements Single Responsibility Principle.
    """

    def __init__(self, app):
        self.app = app
        from services.settings_service import SettingsService

        self.settings_service = SettingsService()

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the specific command logic."""
        pass

    async def _send_message(self, update: Update, text: str, thread_id: int | None = None):
        """Common message sending with thread support."""
        await update.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            message_thread_id=thread_id,
            parse_mode="HTML",
        )

    def _get_user_info(self, update: Update):
        """Get effective user information."""
        from services.user_service import get_effective_user

        return get_effective_user(update.effective_user.id, tg_user=update.effective_user)

    def _clean_user_state(self, uid: int, keys_to_remove: list = None):
        """Clean user state for specific keys."""
        from core.state_manager import state_manager

        st = state_manager.get_user_state(uid)

        default_keys = ["epub_buffer", "meta_pendiente", "portada_pendiente", "titulo_pendiente", "fb_caption"]

        keys = keys_to_remove or default_keys
        for key in keys:
            st.pop(key, None)

        st["destino"] = uid
        return st
