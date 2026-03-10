"""
handlers/v4/publish_handler.py
--------------------------------
PublishHandlerV4: Permite a administradores encolar EPUBs para publicación.

Comandos:
  /publish <book_hash>           — Encola el libro en todos los canales activos
  /publish <book_hash> <ch_id>   — Encola el libro en un canal específico
  /queue_status                  — Resumen del estado actual de la cola
"""

from telegram import Update
from telegram.ext import ContextTypes

from services.v4.publisher_service import PublisherService

from .base_handler import BaseHandlerV4


class PublishHandlerV4(BaseHandlerV4):
    """Gestión de publicación de libros en canales. Solo para admins."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.publisher_svc = PublisherService()

    # ------------------------------------------------------------------ #
    #  /publish <book_hash> [channel_id]                                  #
    # ------------------------------------------------------------------ #

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Encola un libro para publicación."""
        await self.ensure_user(update)
        uid = update.effective_user.id
        privs = await self.get_privileges(uid)

        if not privs.get("is_admin", False):
            await self.reply(update, "🔒 <b>Solo administradores pueden publicar.</b>")
            return

        args = context.args
        if not args:
            await self.reply(
                update,
                "📡 <b>Publicar libro en canales</b>\n\n"
                "Uso: <code>/publish &lt;book_hash&gt; [channel_id]</code>\n\n"
                "• Sin channel_id → publica en <b>todos</b> los canales activos\n"
                "• Con channel_id → publica en un canal específico",
            )
            return

        book_hash = args[0].strip()
        channel_ids = None
        if len(args) > 1:
            try:
                channel_ids = [int(args[1])]
            except ValueError:
                await self.reply(update, "❌ <code>channel_id</code> debe ser un número entero.")
                return

        progress = await update.effective_message.reply_text(
            "⏳ <b>Encolando publicación...</b>",
            parse_mode="HTML",
        )

        result = await self.publisher_svc.enqueue_book(
            book_hash=book_hash,
            channel_ids=channel_ids,
        )

        if not result.success:
            msg = self._enqueue_error_text(result.reason)
        else:
            ids = ", ".join(f"#{qid}" for qid in result.queue_ids)
            msg = (
                f"✅ <b>Libro encolado correctamente</b>\n\n"
                f"📋 Queue IDs: <code>{ids}</code>\n"
                f"📡 Canales: {len(result.queue_ids)}\n\n"
                f"<i>El mensaje se publicará en ~30 segundos.</i>"
            )

        await progress.edit_text(msg, parse_mode="HTML")

    # ------------------------------------------------------------------ #
    #  /queue_status                                                       #
    # ------------------------------------------------------------------ #

    async def handle_queue_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Muestra un resumen del estado actual de la cola de publicación."""
        await self.ensure_user(update)
        uid = update.effective_user.id
        privs = await self.get_privileges(uid)

        if not privs.get("is_admin", False):
            await self.reply(update, "🔒 <b>Solo administradores pueden ver el estado de la cola.</b>")
            return

        status = await self.publisher_svc.get_queue_status()

        if not status:
            await self.reply(update, "📋 <b>Cola de publicación vacía.</b>")
            return

        lines = ["📊 <b>Estado de la Cola de Publicación</b>\n"]
        icons = {
            "pending": "⏳",
            "publishing": "🔄",
            "sent": "✅",
            "failed": "❌",
        }
        for st, count in sorted(status.items()):
            icon = icons.get(st, "•")
            lines.append(f"{icon} <b>{st.capitalize()}:</b> {count}")

        await self.reply(update, "\n".join(lines))

    @staticmethod
    def _enqueue_error_text(reason: str | None) -> str:
        if reason == "book_not_found":
            return "❌ <b>Libro no encontrado.</b> Verifica el book_hash."
        if reason == "no_active_channels":
            return (
                "⚠️ <b>No hay canales activos configurados.</b>\n\n"
                "Configura al menos un canal en el panel de administración."
            )
        return f"❌ Error al encolar: <code>{reason or 'desconocido'}</code>"
