import logging
from collections.abc import Callable
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from plugins.base_plugin import BasePlugin
from utils.decorators import log_user_action


class ExamplePlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "example"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Plugin de ejemplo con estadísticas y funciones de demo"

    def __init__(self):
        self.download_count = 0
        self.search_count = 0
        self.bot_instance = None

    async def initialize(self, bot_instance) -> bool:
        self.bot_instance = bot_instance
        logging.info(f"Plugin {self.name} inicializado")
        return True

    async def cleanup(self) -> None:
        logging.info(f"Plugin {self.name} desactivado")

    def get_commands(self) -> dict[str, Callable]:
        return {"plugin_stats": self.stats_command, "plugin_help": self.help_command}

    def get_callback_handlers(self) -> dict[str, Callable]:
        return {"^plugin_demo": self.demo_callback}

    @log_user_action("plugin_stats")
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats_text = (
            f"📊 **Estadísticas del Plugin {self.name}**\n\n"
            f"Descargas registradas: {self.download_count}\n"
            f"Búsquedas registradas: {self.search_count}\n"
        )
        keyboard = [[InlineKeyboardButton("🔄 Demo", callback_data="plugin_demo")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            stats_text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            f"🔧 **Ayuda del Plugin {self.name}**\n\n"
            "Comandos disponibles:\n"
            "/plugin_stats - Mostrar estadísticas\n"
            "/plugin_help - Esta ayuda\n\n"
            "Este plugin registra descargas y búsquedas automáticamente."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def demo_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer("¡Plugin funcionando correctamente! ✅")
        await query.edit_message_text(
            f"🎉 Demo del plugin {self.name} ejecutada exitosamente\n\n"
            f"Versión: {self.version}\n"
            f"Descripción: {self.description}",
            parse_mode="Markdown",
        )

    async def on_download_request(
        self, user_id: int, epub_url: str, metadata: dict[str, Any]
    ) -> dict[str, Any] | None:
        self.download_count += 1
        logging.info(
            f"Plugin {self.name}: Descarga #{self.download_count} por usuario {user_id}"
        )
        return {"plugin_download_id": self.download_count, "tracked_by": self.name}

    async def on_download_complete(
        self, user_id: int, epub_url: str, success: bool
    ) -> None:
        status = "exitosa" if success else "fallida"
        logging.info(f"Plugin {self.name}: Descarga {status} para usuario {user_id}")
