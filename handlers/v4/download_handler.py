"""
handlers/v4/download_handler.py
---------------------------------
DownloadHandlerV4: procesa el callback de descarga de un EPUB.

Flujo de usuario:
  Usuario pulsa botón "Descargar" en Mini App o callback inline
    → El callback_data contiene: "dl_v4:<book_hash>"
    → DownloadService.prepare_download() verifica límites y localiza el archivo
    → Si OK: send_document() con el EPUB
    → Si NOK: mensaje de error claro con el motivo

Implementa manejo de:
  - book_not_found: libro no en BD
  - file_not_found: archivo borrado del disco
  - daily_limit_reached: límite diario alcanzado
  - user_not_found: usuario no registrado (no debería ocurrir)
"""

from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.v4.download_service import DownloadService

from .base_handler import BaseHandlerV4

# Prefijo del callback data para descargas V4
DOWNLOAD_CALLBACK_PREFIX = "dl_v4:"


class DownloadHandlerV4(BaseHandlerV4):
    """
    Procesa solicitudes de descarga de EPUBs.
    Puede ser invocado desde:
      - Callback query: botón inline "Descargar"
      - Comando /download <book_hash>
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.download_svc = DownloadService()

    # ------------------------------------------------------------------ #
    #  Entry points                                                        #
    # ------------------------------------------------------------------ #

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Entry point para el comando /download <book_hash>."""
        await self.ensure_user(update)

        args = context.args
        if not args:
            await self.reply(
                update,
                "📥 <b>Descarga de EPUB</b>\n\nUso: <code>/download &lt;book_hash&gt;</code>\n\n"
                "💡 Usa la Mini App para seleccionar un libro y descargarlo directamente.",
            )
            return

        book_hash = args[0].strip()
        await self._execute_download(update, context, book_hash)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Entry point para callback queries con data 'dl_v4:<book_hash>'."""
        query = update.callback_query
        if not query:
            return

        await query.answer()  # Ack inmediato para Telegram

        await self.ensure_user(update)
        book_hash = query.data.removeprefix(DOWNLOAD_CALLBACK_PREFIX)
        await self._execute_download(update, context, book_hash)

    # ------------------------------------------------------------------ #
    #  Core logic                                                          #
    # ------------------------------------------------------------------ #

    async def _execute_download(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        book_hash: str,
    ) -> None:
        """Flujo principal: verificar → localizar → enviar → confirmar."""
        uid = update.effective_user.id
        chat_id = update.effective_chat.id

        # Mensaje de progreso
        progress_msg = await update.effective_message.reply_text(
            "⏳ <b>Preparando tu descarga...</b>",
            parse_mode=ParseMode.HTML,
        )

        result = await self.download_svc.prepare_download(
            telegram_id=uid,
            book_hash=book_hash,
            chat_id=chat_id,
        )

        if not result.success:
            await progress_msg.edit_text(
                self._error_text(result.reason, result),
                parse_mode=ParseMode.HTML,
            )
            return

        # Enviar el archivo EPUB
        try:
            await self._send_epub(update, context, result.filepath, result.book_title)
            await progress_msg.delete()
            self.logger.info(f"[DL OK] user={uid} book={book_hash} size={result.file_size}")
        except Exception as e:
            self.logger.error(f"[DL ERROR] send_document failed: {e}")
            await progress_msg.edit_text(
                "❌ <b>Error al enviar el archivo.</b>\n\n"
                "El archivo existe pero no pudo ser enviado. Inténtalo de nuevo más tarde.",
                parse_mode=ParseMode.HTML,
            )

    async def _send_epub(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        filepath: Path,
        title: str | None,
    ) -> None:
        """Envía el EPUB como documento Telegram."""
        caption = f"📚 <b>{title or 'Libro'}</b>\n\n✅ <i>¡Disfruta la lectura!</i>"
        with open(filepath, "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename=filepath.name,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )

    # ------------------------------------------------------------------ #
    #  Error messages                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _error_text(reason: str | None, result) -> str:
        if reason == "book_not_found":
            return "❌ <b>Libro no encontrado.</b>\n\nEste libro no existe en la base de datos."
        if reason == "file_not_found":
            title = result.book_title or "Libro"
            return (
                f"⚠️ <b>Archivo no disponible: {title}</b>\n\n"
                f"El registro existe pero el archivo EPUB no se encontró en disco.\n"
                f"Esto puede deberse a una reindexación pendiente."
            )
        if reason == "daily_limit_reached":
            limit = result.daily_limit
            today = result.downloads_today
            return (
                f"🚫 <b>Límite diario alcanzado</b>\n\n"
                f"Has descargado <b>{today}/{limit}</b> libros hoy.\n\n"
                f"💡 El límite se reinicia a las <b>00:00 UTC</b>.\n"
                f"¿Quieres más descargas? Considera subir de nivel."
            )
        if reason == "user_not_found":
            return "❓ <b>Usuario no encontrado.</b> Usa /start para registrarte."
        return "❌ <b>Error desconocido.</b> Inténtalo de nuevo más tarde."
