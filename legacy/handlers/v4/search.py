import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.v4.base import BaseHandlerV4, with_services

logger = logging.getLogger(__name__)


class SearchHandlerV4(BaseHandlerV4):
    """
    Handler v4.0 para el comando /search.
    Búsqueda asíncrona de series y libros.
    """

    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        library_service = services["library_service"]
        uid = update.effective_user.id
        st = self.get_user_state(uid)

        # 1. Verificar si hay argumentos (búsqueda directa)
        if context.args:
            term = " ".join(context.args).strip()
            return await self._execute_search(update, context, term, library_service)

        # 2. Si no hay argumentos, pedir término y activar estado
        st["esperando_busqueda"] = True
        await self.send_glass_message(
            update,
            "🔍 <b>Buscador ZeePub v4.0</b>\n\n¿Qué serie o libro estás buscando?\n<i>Escribe el título a continuación:</i>",
        )

    async def _execute_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, term: str, library_service):
        """Lógica de búsqueda interna (ahora asíncrona)."""
        # Por ahora usamos una búsqueda simple por nombre.
        # En el futuro integraremos coincidencias por género o autor.
        from sqlalchemy import select

        from models.library import Series

        query = select(Series).where(Series.name.ilike(f"%{term}%")).limit(10)
        result = await library_service.session.execute(query)
        series = result.scalars().all()

        if not series:
            await self.send_glass_message(update, f"❌ No se encontraron resultados para: <code>{term}</code>")
            return

        text = f"🔎 <b>Resultados para:</b> <code>{term}</code>\n\nSelecciona una coincidencia:"
        keyboard = []
        for s in series:
            # IMPORTANTE: Usar sv| (3 chars) + truncated ID para no exceder 64 bytes
            keyboard.append([InlineKeyboardButton(f"📖 {s.name}", callback_data=f"sv|{s.id[:50]}")])

        await self.send_glass_message(update, text, reply_markup=InlineKeyboardMarkup(keyboard))
