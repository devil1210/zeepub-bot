import json
import logging
from pathlib import Path

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
    raw_update = update.to_dict() if hasattr(update, "to_dict") else {}
    widget_query = raw_update.get("widget_query")

    if not widget_query:
        return

    query_id = widget_query.get("id")
    user = widget_query.get("from", {})
    user_id = user.get("id")
    raw_data = widget_query.get("data", "{}")

    try:
        data = json.loads(raw_data)
    except (json.JSONDecodeError, TypeError):
        data = {"action": raw_data}

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

        # Enviar documento EPUB directamente si está disponible en disco
        if book_id and context.bot and user_id:
            try:
                from services.library_service import LibraryService

                book = await LibraryService.get_book_by_hash(book_id)
                filepath = getattr(book, "filepath", None)
                if filepath:
                    p = Path(filepath)
                    if p.is_file():
                        file_bytes = p.read_bytes()
                        await context.bot.send_document(
                            chat_id=user_id,
                            document=file_bytes,
                            filename=getattr(book, "filename", "libro.epub"),
                            caption=f"📖 <b>{getattr(book, 'title', 'Volumen')}</b>",
                            parse_mode="HTML",
                        )
            except (OSError, RuntimeError) as e:
                logger.warning(f"No se pudo despachar archivo directo tras widget query: {e}")
