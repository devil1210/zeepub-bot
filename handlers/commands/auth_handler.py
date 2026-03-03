# handlers/commands/auth_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class AuthHandler(BaseCommandHandler):
    """
    Handle web authentication commands - changeweb, web_login.
    Single Responsibility: Web interface authentication and access management.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle web authentication commands."""
        thread_id = get_thread_id(update)

        # Route to specific auth function based on context
        if context.args:
            command = context.args[0].lower()

            if command == "changeweb":
                await self._handle_change_web(update, context, thread_id)
            elif command == "web_login":
                await self._handle_web_login(update, context, thread_id)
            else:
                await self._show_auth_help(update, thread_id)
        else:
            await self._show_auth_help(update, thread_id)

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

    async def _handle_web_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE, thread_id: int):
        """Handle /web_login - Generate magic access link."""
        st = self._get_user_state(update.effective_user.id)

        # Generate access link (placeholder implementation)
        access_text = "🔗 <b>Acceso Web Generado</b>\n\n"
        access_text += "Enlace de acceso mágico generado.\n\n"
        access_text += "⏰ Este enlace expirará en 24 horas.\n\n"
        access_text += "🔐 Usa el enlace para acceder a la interfaz web."

        st["web_access_generated"] = True

        await self._send_message(update, access_text, thread_id)

    async def _show_auth_help(self, update: Update, thread_id: int):
        """Show authentication commands help."""
        help_text = "🔐 <b>Autenticación Web</b>\n\n"
        help_text += "Comandos disponibles:\n\n"
        help_text += "• <code>/changeweb</code> - Cambiar interfaz web\n"
        help_text += "• <code>/web_login</code> - Generar enlace de acceso\n\n"
        help_text += "💡 Los enlaces generados expiran en 24 horas."

        await self._send_message(update, help_text, thread_id)

    async def _show_auth_help(self, update: Update, thread_id: int):
        """Show general auth help."""
        help_text = "🔐 <b>Acceso a Interfaces Web</b>\n\n"
        help_text += "Comandos disponibles:\n\n"
        help_text += "• <code>/changeweb</code> - Cambiar entre clásica/nueva\n"
        help_text += "• <code>/web_login</code> - Generar enlace de acceso\n\n"
        help_text += "🌐 Accede a las diferentes interfaces del sistema."

        await self._send_message(update, help_text, thread_id)
