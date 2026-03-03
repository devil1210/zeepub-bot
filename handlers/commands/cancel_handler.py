# handlers/commands/cancel_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class CancelHandler(BaseCommandHandler):
    """
    Handle /cancel command - Clean user state and cancel operations.
    Single Responsibility: State management and operation cancellation.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel: limpia estado, borra menús y confirma cancelación."""
        uid = update.effective_user.id
        st = self._get_user_state(uid)
        thread_id = get_thread_id(update)

        if not st:
            no_activity_text = (
                "✨ <b>Tu estado está limpio</b>\n\nNo hay operaciones activas en este momento. ¡Todo en orden! 👌"
            )
            await self._send_message(update, no_activity_text, thread_id)
            return

        # Build cancellation confirmation
        cancel_text = "🚫 <b>Operación Cancelada</b>\n\n"
        cancel_text += "He limpiado tus procesos temporales:\n\n"

        cancelled_items = []
        if st.get("epub_buffer"):
            cancelled_items.append("📤 Subida de EPUB")
        if st.get("meta_pendiente"):
            cancelled_items.append("📝 Edición de metadatos")
        if st.get("portada_pendiente"):
            cancelled_items.append("🖼️ Confirmación de portada")
        if st.get("titulo_pendiente"):
            cancelled_items.append("📋 Asignación de título")

        if cancelled_items:
            for item in cancelled_items:
                cancel_text += f"• {item}\n"
        else:
            cancel_text += "• No había procesos en curso\n"

        cancel_text += "\n✨ <b>Estado listo para una nueva aventura.</b>\n"
        cancel_text += "💡 Usa /catalog para explorar el catálogo."

        # Clean all state
        self._clean_user_state(uid)

        await self._send_message(update, cancel_text, thread_id)
