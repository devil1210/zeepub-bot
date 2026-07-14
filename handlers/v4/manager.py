from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from .callbacks import CallbackHandlerV4
from .catalog import CatalogHandlerV4
from .publish import PublishHandlerV4
from .search import SearchHandlerV4
from .start import StartHandlerV4
from .system import SystemHandlerV4


class HandlerManagerV4:
    """
    Clase encargada de registrar todos los handlers v4.0 en la aplicación.
    """

    def __init__(self, app: Application):
        self.app = app

        # Instanciar Handlers
        self.start_h = StartHandlerV4(app)
        self.catalog_h = CatalogHandlerV4(app)
        self.search_h = SearchHandlerV4(app)
        self.system_h = SystemHandlerV4(app)
        self.callback_h = CallbackHandlerV4(app)
        self.publish_h = PublishHandlerV4(app)

    def register(self):
        """Registra los comandos y callbacks v4.0."""
        # Comandos (Prioridad alta para el refactor)
        self.app.add_handler(CommandHandler("start", self.start_h.handle))
        self.app.add_handler(CommandHandler(["catalog", "menu", "inicio", "ayuda", "help"], self.start_h.handle))
        self.app.add_handler(CommandHandler(["search", "buscar"], self.search_h.handle))
        self.app.add_handler(CommandHandler("status", self.system_h.handle_status))
        self.app.add_handler(CommandHandler("cancel", self.system_h.handle_cancel))
        self.app.add_handler(CommandHandler("evil", self.system_h.handle_evil))
        self.app.add_handler(CommandHandler("destino", self.system_h.handle_destino))
        self.app.add_handler(CommandHandler("upload", self.publish_h.handle))

        from telegram.ext import MessageHandler, filters

        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.system_h.handle_message))

        # Callback Queries
        # Nota: En v4.0 usamos patrones específicos para evitar colisiones con legacy si conviven
        # Pero como es un Deep Refactor, v4.0 tomará el control.
        self.app.add_handler(CallbackQueryHandler(self.callback_h.handle))

        print("[OK] Handlers ZeePub v4.0 registrados correctamente.")
