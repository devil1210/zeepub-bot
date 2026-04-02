# handlers/commands/plugins_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class PluginsHandler(BaseCommandHandler):
    """
    Handle /plugins command - List active plugins and their versions.
    Single Responsibility: Plugin management and system information.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /plugins: lista plugins activos."""
        pm = getattr(self.app, "plugin_manager", None)

        if not pm:
            no_plugins_text = "🔌 <b>Sin Plugins Activos</b>\n\n"
            no_plugins_text += "No hay complementos activos en el sistema.\n\n"
            no_plugins_text += "💡 Contacta al administrador para activar plugins."

            await self._send_message(update, no_plugins_text)
            return

        # Get active plugins
        plugins_info = self._get_active_plugins(pm)

        # Build plugins list message
        plugins_text = f"🔌 <b>Plugins Activos ({len(plugins_info)})</b>\n\n"

        for plugin in plugins_info:
            safe_name = plugin.get("name", "Desconocido").replace("<", "&lt;").replace(">", "&gt;")
            version = plugin.get("version", "N/A")
            description = plugin.get("description", "Sin descripción")

            plugins_text += f"📦 <b>{safe_name}</b> v{version}\n"
            plugins_text += f"   📝 {description}\n\n"

        plugins_text += "💡 <b>Gestión:</b>\n"
        plugins_text += "• Los plugins son gestionados por administradores\n"
        plugins_text += "• Contacta al admin para activar/desactivar plugins"

        await self._send_message(update, plugins_text)

    def _get_active_plugins(self, plugin_manager) -> list:
        """Get list of active plugins with their information."""
        # This would integrate with the actual plugin manager
        # For now, returning placeholder data

        return [
            {"name": "ZeePub Core", "version": "2.0.0", "description": "Sistema principal de gestión de biblioteca"},
            {"name": "Telegram Integration", "version": "1.5.0", "description": "Conexión con bot de Telegram"},
            {"name": "Web Interface", "version": "1.0.0", "description": "Interfaz web para acceso remoto"},
        ]
