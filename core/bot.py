# core/bot.py

import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
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


class ZeePubApplication(Application):
    """Subclase de Application para permitir atributos personalizados."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plugin_manager = None


class ZeePubBot:
    """Clase principal del bot."""

    def __init__(self):
        token = config.TELEGRAM_TOKEN
        self._initialized = False  # Track successful initialization

        # Inicializar la aplicación con config de red optimizada pero segura
        # El default de 5s connect provoca Timeouts en redes lentas/VPN
        trequest = HTTPXRequest(
            connection_pool_size=20,
            connect_timeout=30.0,  # Aumentado de default 5.0s -> 30.0s
            read_timeout=30.0,
            write_timeout=30.0,
            pool_timeout=30.0,
        )

        self.app = (
            ApplicationBuilder()
            .application_class(ZeePubApplication)
            .token(token)
            .request(trequest)
            .build()
        )

        self.plugin_manager = PluginManager()

        # Usar nuevo ErrorHandler
        self.app.add_error_handler(ErrorHandler.handle_error)

        # attach plugin manager to app so handlers can access it
        self.app.plugin_manager = self.plugin_manager

        # Metrics Middleware (Group -1 to run first)
        self.app.add_handler(TypeHandler(Update, self._metrics_middleware), group=-1)

        # Comandos
        self.command_handlers = CommandHandlers(self.app)
        # Handlers are registered in CommandHandlers.__init__
        # Total pages
        self.app.add_handler(CallbackQueryHandler(set_destino, pattern="^destino"))
        self.app.add_handler(CallbackQueryHandler(buscar_epub, pattern="^buscar"))
        self.app.add_handler(CallbackQueryHandler(abrir_zeepubs, pattern="^abrir"))

        self.app.add_handler(CallbackQueryHandler(button_handler), group=1)

        # Mensajes de texto
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_texto)
        )

        # JSON Upload Handler
        from handlers.message_handlers import handle_json_upload, handle_donation_proof

        self.app.add_handler(
            MessageHandler(
                filters.Document.MimeType("application/json"), handle_json_upload
            )
        )
        # Donation Proof Handler (Photo or Document)
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO | filters.Document.ALL, handle_donation_proof
            )
        )

    def start(self):
        """Arranca el bot en polling (bloqueante, modo legacy)."""
        logger.info("Bot iniciado, entrando en polling...")

        # Run initialization in background before starting polling
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(self.initialize())
        self.app.run_polling()
        loop.run_until_complete(session_manager.close())

    async def initialize(self):
        """Inicializa la aplicación (para uso con API)."""
        # 0. Inicializar Base de Datos primero
        from core.db_manager import db_manager
        from core.metrics_db import metrics_db
        try:
            await db_manager.initialize()
            await metrics_db.initialize()
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {e}")
            # Continuamos, pero es probable que fallen cosas después

        max_retries = 5
        retry_delay = 5
        bot_initialized = False
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Intentando inicializar bot (intento {attempt + 1}/{max_retries})..."
                )
                await self.app.initialize()

                # Verify bot is actually ready by accessing bot.id
                try:
                    _ = self.app.bot.id
                    logger.info(
                        f"Bot inicializado exitosamente (ID: {self.app.bot.id})."
                    )
                    bot_initialized = True
                    break
                except RuntimeError as e:
                    if "not properly initialized" in str(e):
                        logger.warning("Bot marcado como initialized pero ExtBot no está listo. Reintentando...")
                        # Force a new initialization attempt
                        await asyncio.sleep(retry_delay)
                        continue
                    raise

            except Exception as e:
                # Check if it's already initialized (happens on retry)
                if "already initialized" in str(e).lower():
                    logger.info("Bot ya estaba marcado como inicializado, verificando estado...")
                    # Try to access bot.id to verify it's really ready
                    try:
                        _ = self.app.bot.id
                        logger.info(f"Bot verificado correctamente (ID: {self.app.bot.id}).")
                        bot_initialized = True
                        break
                    except RuntimeError:
                        logger.warning("Bot marcado como initialized pero ExtBot no está listo. Continuando con error original...")
                        # Can't reinitialize, but bot isn't ready
                        pass

                if attempt < max_retries - 1:
                    wait = retry_delay * (attempt + 1)
                    logger.warning(f"Fallo en initialize (intento {attempt + 1}): {e}. Reintentando en {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Error crítico: No se pudo inicializar el bot tras {max_retries} intentos: {e}")
                    self._initialized = False
                    return

        if not bot_initialized:
            logger.error("Bot no se pudo inicializar correctamente")
            self._initialized = False
            return

        self._initialized = True

        # Initialize plugins explicitely to ensure they are loaded
        try:
            await self.plugin_manager.initialize(self.app)
        except Exception as e:
            logger.error(f"CRITICAL: Error initializing plugins: {e}", exc_info=True)
            # Safe Mode: Register emergency update handler
            try:
                from telegram.ext import CommandHandler

                async def emergency_update_handler(update, context):
                    uid = update.effective_user.id
                    if uid not in config.ADMIN_USERS:
                        return

                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ <b>MODO SEGURO ACTIVADO</b>\n\nEl sistema de plugins falló al iniciar. Intentando actualización de emergencia...",
                        parse_mode="HTML"
                    )

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
                    except Exception as ex:
                        logger.warning(f"Could not notify admin {admin_id} of safe mode: {ex}")
            except Exception as e2:
                logger.error(f"FATAL: Could not register emergency handler: {e2}")

    async def start_async(self):
        """Inicia el bot y el polling de forma asíncrona (para uso con API)."""
        await self.app.start()

        # Robust polling start with retries for NetworkError
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Iniciando polling (intento {attempt + 1}/{max_retries})...")
                await self.app.updater.start_polling()
                logger.info("Bot iniciado en modo asíncrono (API).")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Error iniciando polling: {e}. Reintentando en {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"No se pudo iniciar polling tras {max_retries} intentos: {e}")
                    raise

        # Inicializar schedulers y updates usando BotInitializer
        await BotInitializer.initialize_schedulers(self.app)
        await BotInitializer.check_update_state(self.app.bot)

    async def stop_async(self):
        """Detiene el bot de forma asíncrona."""
        if self.app.updater:
            await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()
        await session_manager.close()
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
            except Exception as e:
                logger.debug(f"Error in metrics middleware: {e}")
