from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.v4.base import BaseHandlerV4, with_services


class CatalogHandlerV4(BaseHandlerV4):
    """
    Handler v4.0 para el comando /catalog.
    Exploración de la biblioteca local.
    """

    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        library_service = services["library_service"]

        # 1. Obtener series (paginación inicial)
        series_list = await library_service.get_all_series(limit=10)

        if not series_list:
            await self.send_glass_message(
                update, "📭 <b>La biblioteca está vacía.</b>\nUsa /upload si eres publicador."
            )
            return

        text = "📚 <b>Catálogo ZeePub v4.0</b>\n\nSelecciona una obra para ver sus detalles:"

        keyboard = []
        for s in series_list:
            # Usamos el hash o ID para la callback
            keyboard.append([InlineKeyboardButton(f"📖 {s.name}", callback_data=f"series_view|{s.id}")])

        # Paginación básica (Placeholder)
        if len(series_list) == 10:
            keyboard.append([InlineKeyboardButton("➡️ Siguiente", callback_data="catalog|1")])

        await self.send_glass_message(update, text, reply_markup=InlineKeyboardMarkup(keyboard))
