import logging

from telegram import Update
from telegram.ext import ContextTypes

from handlers.v4.base import BaseHandlerV4, with_services
from repositories.download_repository import DownloadRepository
from services.cover_service import send_doc_bytes
from services.v4.ui_service import UIServiceV4

logger = logging.getLogger(__name__)


class CallbackHandlerV4(BaseHandlerV4):
    """
    Manejador centralizado de callbacks para la arquitectura v4.0.
    Coordina la navegación entre menús, catálogo y descargas.
    """

    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        query = update.callback_query
        data = query.data

        library_service = services["library_service"]
        services["user_service"]

        # 1. Asegurar que el query sea respondido
        try:
            await query.answer()
        except Exception:
            pass

        # 2. Dispatcher de navegación
        try:
            if data == "main_menu":
                text, markup = await UIServiceV4.render_main_menu()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("catalog|"):
                page = int(data.split("|")[1])
                series_list = await library_service.get_all_series(skip=page * 10, limit=10)
                text, markup = await UIServiceV4.render_series_list(series_list, page=page)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("sv|"):
                series_id = data.split("|")[1]
                series = await library_service.get_series_details(series_id)
                if not series:
                    await query.answer("⚠️ Serie no encontrada.", show_alert=True)
                    return
                # El series_id real puede ser más largo si se buscó por prefijo
                real_series_id = series.id
                books = await library_service.get_books_by_series(real_series_id)
                text, markup = await UIServiceV4.render_series_details(series, books)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("bv|"):
                book_id = data.split("|")[1]
                # Usar repositorio vía library_service si es posible, o búsqueda por prefijo
                book = (
                    await library_service.book_repo.get_by_id_prefix(book_id)
                    if len(book_id) < 64
                    else await library_service.book_repo.get_by_id(book_id)
                )

                if not book:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return

                text, markup = await UIServiceV4.render_book_details(book)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("bd|"):
                book_id = data.split("|")[1]
                user_id = update.effective_user.id

                # Obtener libro
                book = await library_service.book_repo.get_by_id_prefix(book_id)
                if not book:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return

                await query.answer("⚡️ Iniciando descarga...", show_alert=False)

                # Registrar descarga
                download_repo = DownloadRepository(session=services["library_service"].session)
                await download_repo.add_download(
                    user_id=user_id, title=book.title, book_hash=book.id, series_hash=book.series_id
                )

                # Enviar archivo (flujo v3)
                caption = f"📕 <b>{book.title}</b>\n🏷️ Hash: <code>{book.id[:8]}</code>"
                await send_doc_bytes(
                    context.bot,
                    update.effective_chat.id,
                    caption,
                    book.filepath,
                    filename=book.filename or f"{book.title}.epub",
                    parse_mode="HTML",
                )

                # Notificar éxito
                await query.answer("🚀 ¡Archivo enviado con éxito!", show_alert=False)

            elif data == "user_status":
                user_service = services["user_service"]
                user_data = await user_service.get_effective_user(update.effective_user.id)
                text, markup = await UIServiceV4.render_user_status(user_data)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "settings_menu":
                text, markup = await UIServiceV4.render_settings_menu()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "web_access":
                from config.config_settings import config

                text, markup = await UIServiceV4.render_web_access(config.WEBAPP_URL)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "search_init":
                text, markup = await UIServiceV4.render_search_init()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "buscar":
                # Delegar al search_handler pidiendo el término (activará el estado)
                from handlers.v4.search import SearchHandlerV4

                search_h = SearchHandlerV4(self.app)
                await search_h.handle(update, context)

            elif data.startswith("destino|"):
                _, destino = data.split("|", 1)
                uid = update.effective_user.id
                st = self.get_user_state(uid)

                # Manejar destino
                if destino == "aqui":
                    st["destino"] = update.effective_chat.id
                elif destino == "otro":
                    st["esperando_destino_manual"] = True
                    await query.edit_message_text(
                        "✏️ <b>Escribe el @usuario o ID del chat destino:</b>", parse_mode="HTML"
                    )
                    return
                else:
                    st["destino"] = destino  # @canal_id

                await query.answer(f"✅ Destino establecido: {destino}")
                # Volver al menú principal tras configurar
                text, markup = await UIServiceV4.render_main_menu()
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "close_menu":
                await query.message.delete()

            else:
                logger.info(f"Callback no manejado en v4.0: {data}")
                # Podríamos delegar a handlers legacy aquí si es necesario

        except Exception as e:
            logger.error(f"Error procesando callback v4.0 {data}: {e}", exc_info=True)
            await query.answer("❌ Error en la navegación.", show_alert=True)
