# handlers/commands/admin_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class AdminHandler(BaseCommandHandler):
    """
    Handle admin-only commands - evil, changeweb, acceso_web.
    Single Responsibility: Administrative operations and system management.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin commands - evil, changeweb, acceso_web."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        # Check admin permissions
        if not self._is_admin(uid):
            await self._send_admin_denied(update, thread_id)
            return

        # Route to specific admin function based on context
        if context.args:
            command = context.args[0].lower()

            if command == "evil":
                await self._handle_evil_mode(update, context, thread_id)
            elif command == "changeweb":
                await self._handle_change_web(update, context, thread_id)
            elif command == "acceso_web":
                await self._handle_web_access(update, context, thread_id)
            else:
                await self._show_admin_help(update, thread_id)
        else:
            await self._show_admin_help(update, thread_id)

    def _is_admin(self, uid: int) -> bool:
        """Check if user has admin privileges."""
        return uid in self.settings_service.get_admin_users()

    async def _send_admin_denied(self, update: Update, thread_id: int):
        """Send admin access denied message."""
        denied_text = "🚫 <b>Acceso Denegado</b>\n\n"
        denied_text += "Este comando está disponible solo para administradores.\n\n"
        denied_text += "🔐 Si necesitas acceso, contacta al administrador del sistema."

        await self._send_message(update, denied_text, thread_id)

    async def _handle_evil_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE, thread_id: int):
        """Handle /evil - Enable maintenance mode."""
        st = self._get_user_state(update.effective_user.id)

        st["evil_mode"] = True
        st["msg_esperando_pwd"] = update.message.message_id

        evil_text = "🔧 <b>Modo Mantenimiento Activado</b>\n\n"
        evil_text += "El bot ahora está en modo mantenimiento.\n\n"
        evil_text += "🔐 <b>Para desactivar:</b>\n"
        evil_text += "Responde a este mensaje con la contraseña de administrador."

        await self._send_message(update, evil_text, thread_id)

    async def _handle_change_web(self, update: Update, context: ContextTypes.DEFAULT_TYPE, thread_id: int):
        """Handle /changeweb - Switch between web interfaces."""
        st = self._get_user_state(update.effective_user.id)

        # Toggle web interface
        current_web = st.get("web_interface", "classic")
        new_web = "new" if current_web == "classic" else "classic"

        st["web_interface"] = new_web

        change_text = "🌐 <b>Interfaz Web Cambiada</b>\n\n"
        change_text += f"Interfaz actual: <b>{'Clásica' if new_web == 'classic' else 'Nueva'}</b>\n"
        change_text += f"Nueva interfaz: <b>{'Nueva' if new_web == 'new' else 'Clásica'}</b>\n\n"
        change_text += "✅ Cambio aplicado correctamente."

        await self._send_message(update, change_text, thread_id)

    async def _handle_web_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE, thread_id: int):
        """Handle /acceso_web - Generate magic access link."""
        st = self._get_user_state(update.effective_user.id)

        # Generate access link (placeholder implementation)
        access_text = "🔗 <b>Acceso Web Generado</b>\n\n"
        access_text += "Enlace de acceso mágico generado.\n\n"
        access_text += "⏰ Este enlace expirará en 24 horas.\n\n"
        access_text += "🔐 Usa el enlace para acceder a la interfaz web."

        st["web_access_generated"] = True

        await self._send_message(update, access_text, thread_id)

    async def _show_admin_help(self, update: Update, thread_id: int):
        """Show admin commands help."""
        help_text = "🔧 <b>Comandos de Administrador</b>\n\n"
        help_text += "• <code>/evil</code> - Activar modo mantenimiento\n"
        help_text += "• <code>/changeweb</code> - Cambiar interfaz web\n"
        help_text += "• <code>/acceso_web</code> - Generar enlace de acceso\n\n"
        help_text += "💡 Usa <code>/evil contraseña</code> para desactivar modo mantenimiento."

        await self._send_message(update, help_text, thread_id)

    async def _show_admin_help(self, update: Update, thread_id: int):
        """Show general admin help."""
        help_text = "🔧 <b>Panel de Administración</b>\n\n"
        help_text += "Comandos disponibles:\n\n"
        help_text += "• <code>/admin evil</code> - Modo mantenimiento\n"
        help_text += "• <code>/admin changeweb</code> - Cambiar interfaz\n"
        help_text += "• <code>/admin acceso_web</code> - Acceso web\n\n"
        help_text += "🔐 Requiere privilegios de administrador."

        await self._send_message(update, help_text, thread_id)
