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

        # Inicializar la aplicación con config de red optimizada pero segura
        # El default de 5s connect provoca Timeouts en redes lentas/VPN
        trequest = HTTPXRequest(
            connection_pool_size=20,
            connect_timeout=15.0,  # Aumentado de default 5.0s -> 15.0s
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0,
        )

        self.app = ApplicationBuilder().token(token).request(trequest).build()

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
            logger.error(f"CRITICAL: Error initializing plugins: {e}", exc_info=True)
            # Safe Mode: Register emergency update handler
            try:
                from telegram.ext import CommandHandler
                from plugins.system_manager_plugin import SystemManagerPlugin

                # Instantiate a temporary SystemManager to access its update logic
                # or define a minimal standalone fallback function.
                # Using a standalone function is safer to avoid recursive dependency errors.
                
                async def emergency_update_handler(update, context):
                    uid = update.effective_user.id
                    if uid not in config.ADMIN_USERS:
                        return
                    
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ <b>MODO SEGURO ACTIVADO</b>\n\nEl sistema de plugins falló al iniciar. Intentando actualización de emergencia...",
                        parse_mode="HTML"
                    )
                    
                    # Glue code to trigger update
                    # Reusing the existing update logic from SystemManager might be risky if imports failed.
                    # But typically SystemManagerPlugin is fine, passing a class method should work if the file parses.
                    
                    # Let's try to manually trigger the same logic sequence
                    try:
                        from services.maintenance_service import trigger_watchtower_update
                        success, msg = await trigger_watchtower_update()
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode="HTML")
                    except Exception as ex:
                        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Error crítico en update: {ex}")

                self.app.add_handler(CommandHandler("update_system", emergency_update_handler))
                
                # Notify admins of Safe Mode
                for admin_id in config.ADMIN_USERS:
                    try:
                        await self.app.bot.send_message(
                            chat_id=admin_id,
                            text=f"🚨 <b>ALERTA CRÍTICA</b>\nEl bot inició en <b>MODO SEGURO</b> debido a un error en los plugins:\n\n<pre>{str(e)}</pre>\n\nUsa /update_system para intentar reparar.",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
            except Exception as e2:
                logger.error(f"FATAL: Could not register emergency handler: {e2}")

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
