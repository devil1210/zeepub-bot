# handlers/commands/search_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.decorators import rate_limit
from utils.helpers import get_thread_id, is_command_for_bot

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class SearchHandler(BaseCommandHandler):
    """
    Handle /search command - Search EPUBs with term or request specific book.
    Single Responsibility: Search functionality and results display.
    """

    @rate_limit("search", max_requests=30, window_seconds=60)
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search: busca EPUB con término inline o pide uno."""
        # En grupos con múltiples bots, ignorar si el comando no es para este bot
        bot_username = context.bot.username

        if not is_command_for_bot(update.message.text, bot_username):
            return

        # Parse search arguments
        args = context.args

        # Parse search arguments
        args = context.args
        if not args:
            await self._show_search_help(update, context, get_thread_id(update))
            return

        search_term = " ".join(args)

        # Try to find exact match first
        await self._search_by_term(update, context, search_term, get_thread_id(update))

    async def _show_search_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE, thread_id: int):
        """Show search help and options."""
        help_text = "🔍 <b>Búsqueda de EPUBs</b>\n\n💡 <b>Formas de buscar:</b>\n\n"

        await self._send_message(update, help_text, thread_id)

    async def _search_by_term(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str, thread_id: int
    ):
        """Busca series por término y muestra los resultados."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        from services.library_service import LibraryService

        # Usar la misma lógica que la Mini App: buscar SERIES
        data = await LibraryService.search_series(search_term, page=1, items_per_page=10)
        results = data.get("results", [])
        total = data.get("totalItems", 0)

        if not results:
            no_results_text = (
                f"🔍 <b>¡Vaya! No encontré nada para:</b> <code>{search_term}</code>\n\n"
                f"💡 <i>¿Quizás con una palabra clave diferente o revisando las tildes?</i>\n\n"
                f"🔗 También puedes navegar por el catálogo completo en la Mini App."
            )
            await self._send_message(update, no_results_text, thread_id)
            return

        # Formatear resultados
        results_text = f"🔍 <b>Series encontradas para:</b> <code>{search_term}</code>\n"
        results_text += f"✨ Total: {total} series.\n\n"

        for i, series in enumerate(results[:10], 1):
            title = series.get("title", series.get("series", "Sin título"))
            author = series.get("author", "Desconocido")
            count = series.get("book_count", 0)
            results_text += f"{i}. 📁 <b>{title}</b>\n"
            results_text += f"   ✍️ {author} | 📚 {count} vol.\n\n"

        if total > 10:
            results_text += f"<i>... y {total - 10} resultados más.</i>\n\n"

        results_text += "💡 <i>Usa la Mini App para explorar los volúmenes y descargar.</i>"

        # Añadir botón para abrir la Mini App
        keyboard = [[InlineKeyboardButton("🚀 Abrir en Mini App", url=f"https://t.me/{context.bot.username}/app")]]

        await self._send_message(update, results_text, thread_id, reply_markup=InlineKeyboardMarkup(keyboard))
