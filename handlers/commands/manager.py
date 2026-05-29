# handlers/commands/manager.py

import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from handlers.commands.start_handler import StartHandler
from handlers.commands.catalog_handler import CatalogHandler
from handlers.commands.search_handler import SearchHandler
from handlers.commands.status_handler import StatusHandler
from handlers.commands.cancel_handler import CancelHandler
from handlers.commands.evil_handler import EvilHandler
from handlers.commands.plugins_handler import PluginsHandler
from handlers.commands.auth_handler import AuthHandler
from handlers.commands.callbacks_handler import CallbackHandlerV6
from core.state_manager import state_manager

logger = logging.getLogger(__name__)


class HandlerManagerV6:
    """
    Coordinating manager responsible for registering all modern v6 commands,
    unified callback handlers, and message interceptors in the Telegram bot application.
    """

    def __init__(self, app: Application):
        self.app = app

        # Instanciar Handlers de la v6
        self.start_h = StartHandler(app)
        self.catalog_h = CatalogHandler(app)
        self.search_h = SearchHandler(app)
        self.status_h = StatusHandler(app)
        self.cancel_h = CancelHandler(app)
        self.evil_h = EvilHandler(app)
        self.plugins_h = PluginsHandler(app)
        self.auth_h = AuthHandler(app)
        self.callback_h = CallbackHandlerV6(app)

    def register(self):
        """Registra de forma ordenada todos los handlers y comandos de la v6."""
        # 1. Comandos principales de Onboarding y Menú
        self.app.add_handler(CommandHandler("start", self.start_h.handle))
        self.app.add_handler(CommandHandler(["catalog", "menu", "inicio"], self.catalog_h.handle))
        self.app.add_handler(CommandHandler(["ayuda", "help"], self.start_h.handle))

        # 2. Comandos de Búsqueda y Perfil
        self.app.add_handler(CommandHandler(["search", "buscar"], self.search_h.handle))
        self.app.add_handler(CommandHandler("status", self.status_h.handle))

        # 3. Comandos de Sistema y Administración
        self.app.add_handler(CommandHandler("cancel", self.cancel_h.handle))
        self.app.add_handler(CommandHandler("evil", self.evil_h.handle))
        self.app.add_handler(CommandHandler("plugins", self.plugins_h.handle))
        self.app.add_handler(CommandHandler("auth", self.auth_h.handle))

        # 4. MessageHandler para interceptar texto libre (Búsqueda interactiva en chat)
        self.app.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_text_message),
            group=5  # Usar un grupo dedicado para evitar colisiones
        )

        # 5. Callback Queries (Manejador unificado de navegación por botones)
        self.app.add_handler(CallbackQueryHandler(self.callback_h.handle))

        logger.info("🤖 Handlers ZeePub v6.0 registrados exitosamente.")

    async def handle_text_message(self, update, context):
        """Interpreta texto suelto del chat. Si está en 'esperando_busqueda', ejecuta la búsqueda."""
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        # Si el usuario estaba esperando búsqueda interactiva
        if st.get("esperando_busqueda"):
            st["esperando_busqueda"] = False  # Consumir estado
            search_term = update.message.text.strip()
            
            # Delegar al buscador asíncrono pasándole el término ingresado
            await self.search_h._search_by_term(update, context, search_term, get_thread_id(update))
