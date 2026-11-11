# handlers/widget_handlers.py
"""
Manejador de interacciones de usuario provenientes de HTML Widgets (Telegram Bot API 10.4).
Intercepta consultas de widget (widget_query) para acciones interactivas dentro del chat.
"""

import json
import logging
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from config.config_settings import config
from services.widgets.series_carousel_widget import SeriesCarouselWidgetService

logger = logging.getLogger(__name__)


async def handle_widget_interaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa interacciones originadas en HTML Widgets (Bot API 10.4).
    Recibe la acción pulsada en el carrusel (leer o descargar) y responde
    mediante answerWidgetQuery y entrega directa.
    """
    # Extraer widget_query de forma polimórfica (por si PTB no lo tiene tipado como atributo)
    raw_update = update.to_dict() if hasattr(update, "to_dict") else {}
    unhandled = getattr(update, "_unhandled_fields", {}) or {}
    widget_query: dict[str, Any] | None = (
        getattr(update, "widget_query", None)
        or raw_update.get("widget_query")
        or unhandled.get("widget_query")
    )

    if not widget_query:
        return

    query_id = widget_query.get("id") if isinstance(widget_query, dict) else getattr(widget_query, "id", None)
    user_info = widget_query.get("from", {}) if isinstance(widget_query, dict) else getattr(widget_query, "from_user", None)
    user_id = user_info.get("id") if isinstance(user_info, dict) else getattr(user_info, "id", None)
    raw_data = widget_query.get("data", "{}") if isinstance(widget_query, dict) else getattr(widget_query, "data", "{}")

    try:
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except (json.JSONDecodeError, TypeError):
        data = {"action": str(raw_data)}

    action = data.get("action")
    book_id = data.get("book_id")
    volume = data.get("volume", "")

    logger.info(f"Widget Query recibido de usuario {user_id}: {action} (book_id={book_id})")
    token = config.TELEGRAM_TOKEN

    if action == "read":
        # Redirigir al lector Foliate Web Reader en la Mini App / Web Client
        web_url = config.WEBAPP_URL or config.BASE_URL or ""
        target_reader_url = f"{web_url.rstrip('/')}/reader?bookId={book_id}"
        await SeriesCarouselWidgetService.answer_widget_query(
            bot_token=token,
            widget_query_id=query_id,
            url=target_reader_url,
        )
    elif action == "download":
        # Notificar al widget con alerta instantánea
        await SeriesCarouselWidgetService.answer_widget_query(
            bot_token=token,
            widget_query_id=query_id,
            alert_text=f"Preparando entrega del Volumen {volume}...",
        )

        # Enviar documento EPUB directamente mediante enviar_libro_directo
        if book_id and context.bot and user_id:
            try:
                from services.library_service import LibraryService
                from services.telegram_service import enviar_libro_directo

                book = await LibraryService.get_book_by_hash(book_id)
                if book:
                    b_dict = book if isinstance(book, dict) else (book.to_dict() if hasattr(book, "to_dict") else {})
                    filepath = b_dict.get("filepath")
                    title = b_dict.get("title") or f"Volumen {volume}"
                    await enviar_libro_directo(
                        bot=context.bot,
                        user_id=user_id,
                        title=title,
                        download_url=filepath,
                        target_chat_id=user_id,
                        metadata_override=b_dict,
                    )
            except (OSError, RuntimeError, ValueError) as e:
                logger.warning(f"No se pudo despachar libro tras widget query: {e}")
