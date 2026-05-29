# handlers/commands/status_handler.py

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from utils.download_limiter import downloads_left
from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class StatusHandler(BaseCommandHandler):
    """
    Handle /status command - Show user status, level, and download limits.
    Single Responsibility: User information and account status.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status: informa estado interno, nivel de usuario y descargas restantes."""
        thread_id = get_thread_id(update)
        user_info = await self._get_user_info(update)
        st = self._get_user_state(update.effective_user.id)

        if not st:
            no_activity_text = (
                "✨ <b>Tu estado está limpio</b>\n\nNo hay operaciones activas en este momento. ¡Todo en orden! 👌"
            )
            await self._send_message(update, no_activity_text, thread_id)
            return

        # Build status message
        status_text = await self._build_status_message(user_info, st, update.effective_user.id)

        await self._send_message(update, status_text, thread_id)

    async def _build_status_message(self, user_info: dict, st: dict, uid: int) -> str:
        """Build comprehensive status message."""
        level = user_info.get("level", "free")
        role = user_info.get("role")
        is_admin = uid in self.settings_service.get_admin_users()

        # User level and role info
        status_text = "✨ <b>Perfil de Lector - ZeePub</b> ✨\n\n"

        if is_admin:
            status_text += "🔧 <b>Rol:</b> Administrador\n"
        elif level == "staff" and role == "Publicador":
            status_text += "🎯 <b>Rol:</b> Publicador\n"
        elif level == "vip":
            status_text += "⭐ <b>Rol:</b> VIP\n"
        else:
            status_text += "📖 <b>Rol:</b> Usuario Regular\n"

        # Download limits
        downloads_info = await downloads_left(uid)
        if downloads_info:
            status_text += "\n📊 <b>Límites de Descarga:</b>\n"
            status_text += f"• Restantes hoy: {downloads_info.get('remaining_today', 0)}\n"
            status_text += f"• Restantes semana: {downloads_info.get('remaining_week', 0)}\n"
            status_text += f"• Restantes mes: {downloads_info.get('remaining_month', 0)}\n"

            if downloads_info.get("reset_time"):
                reset_time = downloads_info["reset_time"]
                status_text += f"• Reinicio diario: {reset_time.strftime('%H:%M')}\n"

        # Current activity state
        if st:
            status_text += "\n🔄 <b>Estado Actual:</b>\n"

            if st.get("epub_buffer"):
                status_text += "📤 Procesando EPUB para subir\n"
            if st.get("meta_pendiente"):
                status_text += "📝 Metadatos pendientes de revisar\n"
            if st.get("portada_pendiente"):
                status_text += "🖼️ Portada pendiente de confirmar\n"
            if st.get("titulo_pendiente"):
                status_text += "📋 Título pendiente de asignar\n"

        # Account info
        status_text += f"\n📅 <b>Miembro desde:</b> {user_info.get('joined_date', 'Desconocido')}\n"

        if user_info.get("last_download"):
            last_download = user_info["last_download"]
            if isinstance(last_download, datetime):
                status_text += f"📚 <b>Última descarga:</b> {last_download.strftime('%d/%m/%Y %H:%M')}\n"

        # Help footer
        status_text += "\n📚 <b>Bienvenido a ZeePub</b>\n\n"
        status_text += "Tu biblioteca personal de novelas ligeras.\n\n"
        status_text += "📖 <b>Comandos disponibles:</b>\n"
        status_text += "• /cancel - Cancelar operación actual\n"
        status_text += "• /catalog - Explorar biblioteca\n"
        status_text += "• /search - Buscar contenido\n"

        return status_text
