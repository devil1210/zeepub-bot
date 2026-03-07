from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from .callbacks import CallbackHandlerV4
from .catalog import CatalogHandlerV4
from .search import SearchHandlerV4
from .start import StartHandlerV4


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
        self.callback_h = CallbackHandlerV4(app)

    def register(self):
        """Registra los comandos y callbacks v4.0."""
        # Comandos (Prioridad alta para el refactor)
        self.app.add_handler(CommandHandler("start", self.start_h.handle))
        self.app.add_handler(CommandHandler("catalog", self.catalog_h.handle))
        self.app.add_handler(CommandHandler("catalogo", self.catalog_h.handle))
        self.app.add_handler(CommandHandler("search", self.search_h.handle))

        # Callback Queries
        # Nota: En v4.0 usamos patrones específicos para evitar colisiones con legacy si conviven
        # Pero como es un Deep Refactor, v4.0 tomará el control.
        self.app.add_handler(CallbackQueryHandler(self.callback_h.handle))

        print("✅ Handlers ZeePub v4.0 registrados correctamente.")
