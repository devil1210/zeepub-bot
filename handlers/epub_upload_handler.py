"""
ZeePub Bot: EPUB Upload Handler
Manages the process of uploading EPUBs to the library with admin validation.
Refactored to use UploadService and modularized repositories.
"""

import logging
from datetime import datetime
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from repositories.upload_repository import upload_repo
from repositories.user_repository import user_repo
from services.upload_service import upload_service

logger = logging.getLogger(__name__)

# Temporary state for in-progress uploads
# Note: Ideally moved to a persistent store or database if needed across reboots
pending_uploads = {}


class EPUBUploader:
    """Maneja la interacción de Telegram para el upload de EPUBs."""

    def __init__(self):
        self.temp_dir = Path("/tmp/epub_uploads")
        self.temp_dir.mkdir(exist_ok=True)

    async def is_authorized(self, user_id: int) -> bool:
        """Verifica si el usuario es admin o tiene permiso de upload."""
        user = await user_repo.get_by_id(user_id)
        if not user:
            # Fallback to config check if user not in DB (unlikely)
            from config.config_settings import config

            return user_id in config.ADMIN_USERS
        return user.role in ("admin", "mod") or user.can_upload_epub

    async def start_upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia el proceso de upload al recibir el comando."""
        user_id = update.effective_user.id

        if not await self.is_authorized(user_id):
            await update.message.reply_text("❌ Solo admins o usuarios autorizados pueden subir archivos.")
            return

        # Verificar si es respuesta a un mensaje con EPUB
        replied = update.message.reply_to_message
        if not replied or not replied.document or not replied.document.file_name.lower().endswith(".epub"):
            await update.message.reply_text(
                "❌ **Uso incorrecto**\n\nResponde a un mensaje con un archivo EPUB usando `/upload_epub`.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await update.message.reply_text("📥 Descargando y analizando EPUB...")

        try:
            # 1. Descargar
            file = replied.document
            temp_path = self.temp_dir / f"{file.file_name}_{datetime.now().timestamp()}.epub"
            tg_file = await context.bot.get_file(file.file_id)
            await tg_file.download_to_drive(temp_path)

            # 2. Analizar vía Service
            metadata = await upload_service.analyze_epub(temp_path, file.file_name, user_id)

            if not metadata:
                await update.message.reply_text("❌ Error analizando el EPUB. Verifica que sea un archivo válido.")
                if temp_path.exists():
                    temp_path.unlink()
                return

            # 3. Guardar estado pendiente
            upload_id = f"up_{user_id}_{int(datetime.now().timestamp())}"
            pending_uploads[upload_id] = {
                "file_path": str(temp_path),
                "metadata": metadata,
                "user_id": user_id,
                "original_filename": file.file_name,
            }

            # 4. Mostrar vista previa
            await self._send_preview(update, upload_id, metadata)

        except Exception as e:
            logger.error(f"Error in start_upload: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error procesando el EPUB: {str(e)}")

    async def _send_preview(self, update: Update, upload_id: str, metadata: dict):
        """Genera y envía el mensaje de confirmación con metadata."""
        preview = f"""📚 **Vista Previa de EPUB**

📄 **Archivo:** `{metadata.get("original_filename")}`
📖 **Título:** {metadata.get("title")}
✍️ **Autor:** {metadata.get("author")}
📚 **Serie:** {metadata.get("series") or "N/A"}
📖 **Volumen:** {metadata.get("volume") or "N/A"}
🏷️ **Géneros:** {metadata.get("tags", "N/A")}
📁 **Ruta sugerida:** `{metadata.get("suggested_path")}`
"""
        is_duplicate = metadata.get("identity_match", {}).get("exists")
        if is_duplicate:
            preview += f"\n⚠️ **DUPLICADO:** Ya existe en `{metadata['identity_match']['path']}`"
            btn_label = "🔄 Reemplazar / Actualizar"
            callback = f"replace_epub_{upload_id}"
        else:
            preview += "\n✅ Nuevo libro para la biblioteca."
            btn_label = "✅ Aprobar Subida"
            callback = f"approve_epub_{upload_id}"

        keyboard = [
            [
                InlineKeyboardButton(btn_label, callback_data=callback),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"reject_epub_{upload_id}"),
            ],
            [InlineKeyboardButton("📝 Editar Ruta", callback_data=f"edit_path_{upload_id}")],
        ]

        await update.message.reply_text(
            preview, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja las acciones de los botones (aprobar, rechazar, etc)."""
        query = update.callback_query
        await query.answer()

        data = query.data
        parts = data.split("_")
        action = parts[0]
        upload_id = "_".join(parts[2:])  # up_user_timestamp

        if upload_id not in pending_uploads:
            await query.edit_message_text("❌ Sesión de subida expirada o no encontrada.")
            return

        info = pending_uploads[upload_id]

        if action in ("approve", "replace"):
            await self._finalize_upload(query, upload_id, info)
        elif action == "reject":
            if Path(info["file_path"]).exists():
                Path(info["file_path"]).unlink()
            del pending_uploads[upload_id]
            await query.edit_message_text("❌ Upload rechazado y eliminado.")
        elif action == "edit":
            await query.edit_message_text(
                "⚠️ Edición manual de ruta no implementada en esta versión compacta. Usa la sugerida."
            )

    async def _finalize_upload(self, query, upload_id: str, info: dict):
        """Llama al servicio para mover el archivo e indexar."""
        await query.edit_message_text("🔄 Procesando y moviendo archivo...")

        success = await upload_service.finalize_upload(
            Path(info["file_path"]), info["metadata"]["suggested_path"], info["metadata"]
        )

        if success:
            await query.edit_message_text(
                f"✅ **Subida completada con éxito**\n\nEl libro ha sido indexado y está disponible en la librería.\n📍 `{info['metadata']['suggested_path']}`",
                parse_mode=ParseMode.MARKDOWN,
            )
            # Log Historial via Repository (via service ideally but repo is fine)
            await upload_repo.log_history(
                {
                    "user_id": info["user_id"],
                    "filename": info["original_filename"],
                    "book_hash": info["metadata"]["book_hash"],
                    "status": "success",
                    "final_path": info["metadata"]["suggested_path"],
                }
            )
        else:
            await query.edit_message_text("❌ Falló la indexación final. Revisa los logs.")

        if Path(info["file_path"]).exists():
            Path(info["file_path"]).unlink()
        del pending_uploads[upload_id]


# Singleton
epub_uploader = EPUBUploader()


async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await epub_uploader.start_upload(update, context)


async def upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await epub_uploader.handle_callback(update, context)


def setup_upload_handlers(application):
    application.add_handler(CommandHandler("upload_epub", upload_command))
    application.add_handler(CallbackQueryHandler(upload_callback, pattern=r"^(approve|reject|edit|replace)_epub_"))
