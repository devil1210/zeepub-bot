# handlers/commands/catalog_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.library_ui_service import mostrar_menu_principal
from utils.decorators import rate_limit

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class CatalogHandler(BaseCommandHandler):
    """
    Handle /catalog command - Show main library interface.
    Single Responsibility: Library browsing and navigation.
    """

    @rate_limit("catalog", max_requests=5, window_seconds=60)
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /catalog: Muestra el catálogo principal."""
        await mostrar_menu_principal(update, context)
