"""
handlers/v4/search_handler.py
------------------------------
Maneja el comando /search.
V4: Usa LibraryService.search_series desacoplado del modelo V3.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandlerV4


class SearchHandlerV4(BaseHandlerV4):
    """
    /search <término> — Busca series en el catálogo.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.ensure_user(update)

        args = context.args
        if not args:
            await self.reply(
                update,
                "🔍 <b>Búsqueda de Novelas</b>\n\n"
                "Uso: <code>/search &lt;título o autor&gt;</code>\n\n"
                "💡 También puedes buscar directamente desde la Mini App.",
            )
            return

        query = " ".join(args).strip()
        await self._do_search(update, context, query)

    # ------------------------------------------------------------------ #
    async def _do_search(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        query: str,
    ) -> None:
        results = await self.library_svc.search_series(query)
        items = results.get("items", [])
        total = results.get("total", 0)

        if not items:
            await self.reply(
                update,
                f"🔍 No encontré resultados para: <code>{query}</code>\n\n"
                f"💡 Intenta con una palabra diferente o revisa las tildes.",
            )
            return

        lines = [
            f"🔍 <b>Resultados para:</b> <code>{query}</code>",
            f"✨ Total: {total} series\n",
        ]
        for i, s in enumerate(items[:10], 1):
            title = s.get("title", "Sin título")
            count = s.get("book_count", 0)
            lines.append(f"{i}. 📁 <b>{title}</b> — {count} vol.")

        if total > 10:
            lines.append(f"\n<i>... y {total - 10} más. Abre la Mini App para ver todos.</i>")
        else:
            lines.append("\n💡 <i>Usa la Mini App para descargar los volúmenes.</i>")

        keyboard = [
            [
                InlineKeyboardButton(
                    "🚀 Abrir Mini App",
                    url=f"https://t.me/{context.bot.username}/app",
                )
            ]
        ]

        await self.reply(update, "\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
