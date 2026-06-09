# handlers/commands/manager.py

import logging
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from handlers.commands.start_handler import StartHandler
from handlers.commands.catalog_handler import CatalogHandler
from handlers.commands.search_handler import SearchHandler
from handlers.commands.status_handler import StatusHandler
from handlers.commands.cancel_handler import CancelHandler
from handlers.commands.evil_handler import EvilHandler
from handlers.commands.plugins_handler import PluginsHandler
from handlers.commands.auth_handler import AuthHandler
from telegram.ext import InlineQueryHandler
from handlers.commands.callbacks_handler import CallbackHandlerV6
from handlers.commands.inline_handler import InlineQueryHandlerV6
from core.state_manager import state_manager
from utils.helpers import get_thread_id

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
        self.inline_h = InlineQueryHandlerV6(app)

    def register(self):
        """Registra de forma ordenada todos los handlers y comandos de la v6."""
        # 1. Comandos principales de Onboarding y Menú
        self.app.add_handler(CommandHandler("start", self.start_h.handle))
        self.app.add_handler(
            CommandHandler(["catalog", "menu", "inicio"], self.catalog_h.handle)
        )
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
            group=5,  # Usar un grupo dedicado para evitar colisiones
        )

        # 5. Callback Queries (Manejador unificado de navegación por botones)
        self.app.add_handler(CallbackQueryHandler(self.callback_h.handle))

        # 6. Inline Queries (Buscador Inline / Guest Bot)
        self.app.add_handler(InlineQueryHandler(self.inline_h.handle))

        logger.info("🤖 Handlers ZeePub v6.0 registrados exitosamente.")

    async def handle_text_message(self, update, context):
        """Interpreta texto suelto del chat. Si está en 'esperando_busqueda', ejecuta la búsqueda; si no, responde usando IA."""
        if not update.message or not update.message.text:
            return

        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        text = update.message.text.strip()
        thread_id = get_thread_id(update)

        # Si el usuario estaba esperando búsqueda interactiva
        if st.get("esperando_busqueda"):
            st["esperando_busqueda"] = False  # Consumir estado
            await self.search_h._search_by_term(
                update, context, text, thread_id
            )
            return

        # Enviar aviso de "escribiendo..." de Telegram para mejorar la UX
        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing",
                message_thread_id=thread_id
            )
        except Exception:
            pass

        # Procesar consulta conversacional sobre la biblioteca con IA
        from services.ai_chat_service import AIChatService
        response_html = await AIChatService.process_user_query(text)

        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response_html,
                parse_mode="HTML",
                reply_to_message_id=update.message.message_id,
                message_thread_id=thread_id,
                disable_web_page_preview=False,
            )
        except Exception as e:
            logger.error(f"Error al enviar respuesta de IA formateada en HTML: {e}")
            # Fallback en texto plano si falla el parseo HTML de Telegram
            clean_html_text = AIChatService.escape_telegram_html(response_html)
            fallback_text = (
                f"⚠️ Ocurrió un problema de formato. Aquí tienes el contenido de la respuesta:\n\n"
                f"{clean_html_text}"
            )
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=fallback_text,
                    message_thread_id=thread_id,
                )
            except Exception as fe:
                logger.error(f"Error en fallback de mensaje de IA: {fe}")
