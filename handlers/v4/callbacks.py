from telegram import Update
from telegram.ext import ContextTypes
from handlers.v4.base import BaseHandlerV4, with_services
from services.v4.ui_service import UIServiceV4
import logging

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
        uid = update.effective_user.id
        
        library_service = services["library_service"]
        user_service = services["user_service"]
        
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
                series_list = await library_service.get_all_series(skip=page*10, limit=10)
                text, markup = await UIServiceV4.render_series_list(series_list, page=page)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("series_view|"):
                series_id = data.split("|")[1]
                series = await library_service.get_series_details(series_id)
                if not series:
                    await query.answer("⚠️ Serie no encontrada.", show_alert=True)
                    return
                books = await library_service.get_books_by_series(series_id)
                text, markup = await UIServiceV4.render_series_details(series, books)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data.startswith("book_view|"):
                book_id = data.split("|")[1]
                # En el futuro, LibraryService tendrá get_book_details
                from models.library import Book
                from sqlalchemy import select
                query_book = select(Book).where(Book.id == book_id)
                res = await library_service.session.execute(query_book)
                book = res.scalar_one_or_none()
                
                if not book:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return
                
                text, markup = await UIServiceV4.render_book_details(book)
                await query.edit_message_text(text, reply_markup=markup, parse_mode="HTML")

            elif data == "close_menu":
                await query.message.delete()

            else:
                logger.info(f"Callback no manejado en v4.0: {data}")
                # Podríamos delegar a handlers legacy aquí si es necesario
                
        except Exception as e:
            logger.error(f"Error procesando callback v4.0 {data}: {e}", exc_info=True)
            await query.answer("❌ Error en la navegación.", show_alert=True)
