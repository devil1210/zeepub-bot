# handlers/commands/inline_handler.py

import logging
import uuid
from telegram import (
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config.config_settings import config
from services.library_service import LibraryService

logger = logging.getLogger(__name__)


class InlineQueryHandlerV6:
    """
    Handler encargado de procesar las consultas Inline en Telegram.
    Permite buscar series y libros escribiendo @nombre_del_bot [término].
    """

    def __init__(self, app):
        self.app = app

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el evento inline_query de Telegram."""
        inline_query = update.inline_query
        if not inline_query:
            return

        query = inline_query.query.strip()
        results = []

        try:
            # 1. Recuperar candidatos de Series y Libros
            if not query:
                # Si la consulta está vacía, sugerimos los últimos libros añadidos
                recent_data = await LibraryService.get_recent_books(page=1, items_per_page=15)
                books = recent_data.get("items", [])
                
                # Y las series más populares o recientes
                series_data = await LibraryService.search_series(query="", page=1, items_per_page=5)
                series = series_data.get("results", [])
            else:
                # Buscar series que coincidan con la búsqueda
                series_data = await LibraryService.search_series(query, page=1, items_per_page=15)
                series = series_data.get("results", [])

                # Buscar libros individuales que coincidan
                books_data = await LibraryService.search_books(query, page=1, items_per_page=15)
                books = books_data.get("items", [])

            # Dominios base desde la configuración
            webapp_base = config.WEBAPP_URL or f"https://{config.PUBLIC_DOMAIN}/"
            dl_base = f"https://{config.DL_DOMAIN}" if config.DL_DOMAIN else "https://dl.zeepubs.vip"

            # 2. Procesar Series y agregarlas a los resultados inline
            seen_series = set()
            for s in series:
                s_id = s.get("id")
                if not s_id or s_id in seen_series:
                    continue
                seen_series.add(s_id)

                slug = s.get("slug") or s_id
                title = s.get("name")
                author = s.get("author") or "Desconocido"
                desc = s.get("description") or "Sin sinopsis disponible."
                genres = s.get("genres", [])
                genres_str = ", ".join(genres) if genres else "Sin géneros"
                
                # Construir ficha HTML para el mensaje
                # Limitar descripción para evitar superar el límite de caracteres de Telegram
                desc_truncated = desc[:500] + "..." if len(desc) > 500 else desc
                
                # Limpiar texto para prevenir errores de parseo HTML
                clean_title = s.get("name", "").replace("<", "&lt;").replace(">", "&gt;")
                clean_author = author.replace("<", "&lt;").replace(">", "&gt;")
                clean_desc = desc_truncated.replace("<", "&lt;").replace(">", "&gt;")

                message_text = (
                    f"📚 <b>Serie: {clean_title}</b>\n"
                    f"✍️ <i>Autor: {clean_author}</i>\n"
                    f"🏷️ <i>Géneros: {genres_str}</i>\n\n"
                    f"{clean_desc}\n\n"
                    f"🔗 <a href='{webapp_base}series/{slug}'>Ver Ficha en la Web</a>"
                )

                keyboard = [
                    [
                        InlineKeyboardButton(
                            "📖 Ver Ficha en Web App",
                            url=f"{webapp_base}series/{slug}",
                        )
                    ]
                ]

                results.append(
                    InlineQueryResultArticle(
                        id=f"series_{s_id[:20]}_{str(uuid.uuid4())[:8]}",
                        title=f"📚 Serie: {title}",
                        description=f"Por {author} | {genres_str}",
                        thumb_url=s.get("cover_url"),
                        input_message_content=InputTextMessageContent(
                            message_text=message_text,
                            parse_mode="HTML",
                            disable_web_page_preview=False,
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                )

            # 3. Procesar Libros individuales y agregarlos a los resultados
            seen_books = set()
            for b in books:
                b_id = b.get("id") or b.get("hash")
                if not b_id or b_id in seen_books:
                    continue
                seen_books.add(b_id)

                title = b.get("title") or b.get("filename")
                volume = b.get("volume")
                vol_str = f"Volumen {volume}" if volume is not None else "Volumen Único"
                group = b.get("group_siglas") or "Desconocido"
                short_code = b.get("short_link") or b_id
                dl_url = f"{dl_base}/{short_code}"

                clean_title = title.replace("<", "&lt;").replace(">", "&gt;")
                clean_group = group.replace("<", "&lt;").replace(">", "&gt;")

                message_text = (
                    f"📖 <b>Libro: {clean_title}</b>\n"
                    f"💿 <i>{vol_str}</i>\n"
                    f"👥 <i>Traducción: {clean_group}</i>\n\n"
                    f"📥 Enlace de descarga rápida permanente:\n"
                    f"⚡ <a href='{dl_url}'>Descargar archivo EPUB</a>"
                )

                keyboard = [
                    [
                        InlineKeyboardButton("📥 Descargar EPUB", url=dl_url)
                    ]
                ]

                results.append(
                    InlineQueryResultArticle(
                        id=f"book_{b_id[:20]}_{str(uuid.uuid4())[:8]}",
                        title=f"📖 {title} ({vol_str})",
                        description=f"Traducción: {group} | Enlace de descarga directa",
                        thumb_url=b.get("cover_medium") or b.get("cover_low"),
                        input_message_content=InputTextMessageContent(
                            message_text=message_text,
                            parse_mode="HTML",
                            disable_web_page_preview=False,
                        ),
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                )

            # 4. Responder al inline query (limitar a 50 resultados máximo que es el límite de Telegram)
            await inline_query.answer(results[:50], cache_time=300, is_personal=False)

        except Exception as e:
            logger.error(f"Error en InlineQueryHandlerV6 para la consulta '{query}': {e}", exc_info=True)
