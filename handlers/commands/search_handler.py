# handlers/commands/search_handler.py

import logging
from telegram import Update
from telegram.ext import ContextTypes

from utils.decorators import rate_limit
from utils.helpers import get_thread_id, is_command_for_bot
from .base_handler import BaseCommandHandler
from core.state_manager import state_manager
from services.library_service import LibraryService
from services.library_ui_service import mostrar_resultados_locales

logger = logging.getLogger(__name__)


class SearchHandler(BaseCommandHandler):
    """
    Handle /search command - Search EPUBs interactively with inline buttons.
    Supports both direct command arguments and text message fallback search.
    """

    @rate_limit("search", max_requests=30, window_seconds=60)
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search: busca EPUB con término inline o pide uno interactivo."""
        bot_username = context.bot.username
        if update.message and not is_command_for_bot(update.message.text, bot_username):
            return

        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        args = context.args

        # A. Si no hay argumentos, pedir término de búsqueda interactivo con UI Rich Message
        if not args:
            from services.library_ui_service import pedir_termino_busqueda
            await pedir_termino_busqueda(update, context, force_new=True)
            return

        # B. Si hay argumentos, realizar la búsqueda directa
        search_term = " ".join(args).strip()
        await self._search_by_term(update, context, search_term, get_thread_id(update))

    async def _search_by_term(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str, thread_id: int
    ):
        """Busca series y libros por término asíncronamente en Postgres y pinta botones interactivos."""
        try:
            # 1. Buscar Series coincidentes
            data_s = await LibraryService.search_series(search_term, page=1, items_per_page=15)
            series = data_s.get("results", [])

            # 2. Buscar Libros individuales
            data_b = await LibraryService.search_books(search_term, page=1, items_per_page=15)
            books = data_b.get("items", [])

            # 3. Mostrar resultados mediante el maquetador visual premium del catálogo local
            await mostrar_resultados_locales(
                update=update,
                context=context,
                query=search_term,
                series=series,
                books_standalone=books
            )

        except Exception as e:
            logger.error(f"Error ejecutando búsqueda interactiva para '{search_term}': {e}", exc_info=True)
            await self._send_message(
                update,
                "❌ Ocurrió un error al procesar tu búsqueda. Por favor, reintenta en unos instantes.",
                thread_id
            )
