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
            no_activity_text = "ℹ️ No hay operaciones activas para cancelar.\n\n✅ Tu estado está limpio."
            await self._send_message(update, no_activity_text, thread_id)
            return

        # Build cancellation confirmation
        cancel_text = "🚫 <b>Operación Cancelada</b>\n\n"
        cancel_text += "Se han limpiado todos los estados temporales:\n\n"

        cancelled_items = []
        if st.get("epub_buffer"):
            cancelled_items.append("📤 Procesamiento de EPUB")
        if st.get("meta_pendiente"):
            cancelled_items.append("📝 Revisión de metadatos")
        if st.get("portada_pendiente"):
            cancelled_items.append("🖼️ Confirmación de portada")
        if st.get("titulo_pendiente"):
            cancelled_items.append("📋 Asignación de título")

        if cancelled_items:
            for item in cancelled_items:
                cancel_text += f"• {item}\n"
        else:
            cancel_text += "• No había operaciones pendientes\n"

        cancel_text += "\n✅ Estado reiniciado completamente.\n\n"
        cancel_text += "💡 Usa /catalog para comenzar una nueva operación."

        # Clean all state
        self._clean_user_state(uid)

        await self._send_message(update, cancel_text, thread_id)
