# handlers/commands/evil_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class EvilHandler(BaseCommandHandler):
    """
    Handle /evil command - Enable maintenance mode with password protection.
    Single Responsibility: System maintenance and security operations.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /evil: inicia modo privado solicitando contraseña."""
        uid = update.effective_user.id
        st = self._get_user_state(uid)
        thread_id = get_thread_id(update)

        st["evil_mode"] = True
        st["msg_esperando_pwd"] = update.message.message_id

        evil_text = "🔧 <b>Modo Mantenimiento Activado</b>\n\n"
        evil_text += "El bot ahora está en modo mantenimiento.\n\n"
        evil_text += "🔐 <b>Para desactivar:</b>\n"
        evil_text += "Responde a este mensaje con la contraseña de administrador."

        await self._send_message(update, evil_text, thread_id)
