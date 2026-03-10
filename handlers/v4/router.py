"""
handlers/v4/router.py
-----------------------
Registra todos los comandos V4 en la Application de python-telegram-bot.

Uso:
    from handlers.v4.router import register_v4_handlers
    register_v4_handlers(application)
"""

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from .admin_handler import AdminHandlerV4
from .download_handler import DOWNLOAD_CALLBACK_PREFIX, DownloadHandlerV4
from .publish_handler import PublishHandlerV4
from .search_handler import SearchHandlerV4
from .start_handler import StartHandlerV4
from .status_handler import StatusHandlerV4
from .upload_handler import UploadHandlerV4


def register_v4_handlers(app: Application) -> None:
    """
    Registra todos los handlers V4 en la aplicación Telegram.
    Reemplaza los handlers V3 de forma incremental.
    """

    start = StartHandlerV4()
    search = SearchHandlerV4()
    status = StatusHandlerV4()
    admin = AdminHandlerV4()
    download = DownloadHandlerV4()
    publish = PublishHandlerV4()
    upload = UploadHandlerV4()

    app.add_handler(CommandHandler("start", start.handle))
    app.add_handler(CommandHandler("search", search.handle))
    app.add_handler(CommandHandler("status", status.handle))
    app.add_handler(CommandHandler("admin", admin.handle))
    app.add_handler(CommandHandler("download", download.handle))
    app.add_handler(CommandHandler("publish", publish.handle))
    app.add_handler(CommandHandler("queue_status", publish.handle_queue_status))

    # Documentos EPUB → pipeline de ingesta con IA
    app.add_handler(
        MessageHandler(
            filters.Document.MimeType("application/epub+zip") | filters.Document.FileExtension("epub"),
            upload.handle_document,
        )
    )

    # Callback para botones inline de descarga
    app.add_handler(
        CallbackQueryHandler(
            download.handle_callback,
            pattern=f"^{DOWNLOAD_CALLBACK_PREFIX}",
        )
    )
