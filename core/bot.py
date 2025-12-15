# core/bot.py

import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    MessageHandler,
    TypeHandler,
    ContextTypes,
    filters,
)
from config.config_settings import config
from core.session_manager import session_manager
from core.bot_initializer import BotInitializer
from core.error_handler import ErrorHandler
from utils.metrics import metrics
from handlers.command_handlers import CommandHandlers
from handlers.callback_handlers import (
    set_destino,
    buscar_epub,
    abrir_zeepubs,
    button_handler,
)
from handlers.message_handlers import recibir_texto
from plugins.plugin_manager import PluginManager
from telegram.request import HTTPXRequest

logger = logging.getLogger(__name__)


class ZeePubBot:
    """Clase principal del bot."""

    def __init__(self):
        token = config.TELEGRAM_TOKEN

        # Inicializar la aplicación con configuración por defecto (similar a v3.1.3)
        self.app = ApplicationBuilder().token(token).build()

        self.plugin_manager = PluginManager()


        # Usar nuevo ErrorHandler
        self.app.add_error_handler(ErrorHandler.handle_error)

        # attach plugin manager to app so handlers can access it
        setattr(self.app, "plugin_manager", self.plugin_manager)

        # Metrics Middleware (Group -1 to run first)
        self.app.add_handler(TypeHandler(Update, self._metrics_middleware), group=-1)

        # Comandos
        self.command_handlers = CommandHandlers(self.app)
        # Handlers are registered in CommandHandlers.__init__

        # Callbacks
        self.app.add_handler(CallbackQueryHandler(set_destino, pattern="^destino"))
        self.app.add_handler(CallbackQueryHandler(buscar_epub, pattern="^buscar"))
        self.app.add_handler(CallbackQueryHandler(abrir_zeepubs, pattern="^abrir"))

        self.app.add_handler(CallbackQueryHandler(button_handler), group=1)

        # Mensajes de texto
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_texto)
        )

        # JSON Upload Handler
        from handlers.message_handlers import handle_json_upload

        self.app.add_handler(
            MessageHandler(
                filters.Document.MimeType("application/json"), handle_json_upload
            )
        )

    def start(self):
        """Arranca el bot en polling (bloqueante, modo legacy)."""
        logger.info("Bot iniciado, entrando en polling...")
        self.app.run_polling()
        session_manager.close()

    async def initialize(self):
        """Inicializa la aplicación (para uso con API)."""
        await self.app.initialize()
        # Initialize plugins explicitely to ensure they are loaded
        try:
            await self.plugin_manager.initialize(self.app)
        except Exception as e:
            logger.error("Error initializing plugins: %s", e, exc_info=True)

    async def start_async(self):
        """Inicia el bot y el polling de forma asíncrona (para uso con API)."""
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("Bot iniciado en modo asíncrono (API).")

        # Inicializar schedulers y updates usando BotInitializer
        await BotInitializer.initialize_schedulers(self.app.bot)
        await BotInitializer.check_update_state(self.app.bot)

    async def stop_async(self):
        """Detiene el bot de forma asíncrona."""
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        session_manager.close()
        logger.info("Bot detenido (API).")

    async def _metrics_middleware(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Middleware para recolectar métricas básicas."""
        if (
            update.message
            and update.message.text
            and update.message.text.startswith("/")
        ):
            try:
                cmd = update.message.text.split()[0].split("@")[0]
                metrics.inc_command(cmd)
            except Exception:
                pass
