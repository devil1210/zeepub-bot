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
        help_text = "🔍 <b>Búsqueda de EPUBs</b>\n\n" "💡 <b>Formas de buscar:</b>\n\n"

        await self._send_message(update, help_text, thread_id)

    async def _search_by_term(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str, thread_id: int
    ):
        """Perform search by term and show results."""
        # This would integrate with the actual search service
        # For now, showing a placeholder implementation

        from services.library_ui_service import search_library

        results = await search_library(search_term, uid=update.effective_user.id)

        if not results:
            no_results_text = f"🔍 <b>No se encontraron resultados para:</b>\n\n<code>{search_term}</code>\n\n💡 Intenta con otros términos."
            await self._send_message(update, no_results_text, thread_id)
            return

        # Format and show results
        results_text = f"🔍 <b>Resultados para:</b> <code>{search_term}</code>\n\n"

        for i, book in enumerate(results[:10], 1):  # Limit to 10 results
            results_text += f"{i}. 📖 {book.get('title', 'Sin título')}\n"
            results_text += f"   📝 Volumen: {book.get('volume', 'N/A')}\n"
            results_text += f"   👤 Autor: {book.get('author', 'N/A')}\n\n"

        if len(results) > 10:
            results_text += f"\n... y {len(results) - 10} resultados más."

        await self._send_message(update, results_text, thread_id)
