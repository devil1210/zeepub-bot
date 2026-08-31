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

import time


class RateLimiter:
    def __init__(self, limit_window_seconds: int = 10, max_messages: int = 5):
        self.limit_window = limit_window_seconds
        self.max_messages = max_messages
        self.history = {}

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        user_history = self.history.get(user_id, [])
        # Filtrar marcas de tiempo dentro de la ventana de tiempo
        user_history = [ts for ts in user_history if now - ts < self.limit_window]
        if len(user_history) >= self.max_messages:
            return False
        user_history.append(now)
        self.history[user_id] = user_history
        return True


rate_limiter = RateLimiter()


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
        """Registra comandos y callbacks del bot."""
        self.app.add_handler(
            CommandHandler(["start", "menu", "inicio"], self.start_h.handle)
        )
        self.app.add_handler(
            CommandHandler(["catalog", "catalogo", "series"], self.handle_catalog_series)
        )
        self.app.add_handler(
            CommandHandler(["ayuda", "help"], self.handle_help)
        )
        self.app.add_handler(
            CommandHandler(["donar", "vip", "donaciones"], self.handle_donations)
        )
        self.app.add_handler(
            CommandHandler(["reglas", "rules"], self.handle_rules)
        )
        self.app.add_handler(
            CommandHandler(["search", "buscar"], self.search_h.handle)
        )
        self.app.add_handler(
            CommandHandler(["status", "perfil"], self.status_h.handle)
        )
        self.app.add_handler(
            CommandHandler(["cancel", "cancelar"], self.cancel_h.handle)
        )
        self.app.add_handler(CommandHandler("evil", self.evil_h.handle))
        self.app.add_handler(CommandHandler("plugins", self.plugins_h.handle))
        self.app.add_handler(CommandHandler("auth", self.auth_h.handle))
        self.app.add_handler(CommandHandler("test_ai", self.handle_test_ai))
        self.app.add_handler(CommandHandler("setkey", self.handle_setkey))

        # Manejador de texto suelto interceptor (Con prioridad)
        self.app.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_text_message)
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

        # 1. Protección Bot-a-Bot
        if update.effective_user.is_bot:
            return

        chat_type = update.effective_chat.type
        is_group = chat_type in ["group", "supergroup"]
        text = update.message.text.strip()

        # Si estamos en un grupo, solo responder si es mencionado o si es un reply al bot
        if is_group:
            bot_username = context.bot.username
            is_reply_to_bot = (
                update.message.reply_to_message
                and update.message.reply_to_message.from_user
                and update.message.reply_to_message.from_user.id == context.bot.id
            )
            has_mention = bot_username and f"@{bot_username}" in text

            # Si no se menciona al bot ni es un reply al bot, ignorar silenciosamente
            if not is_reply_to_bot and not has_mention:
                return

        uid = update.effective_user.id

        # 2. Rate Limiting (Omitir para Administradores de la configuración)
        from config.config_settings import config

        is_admin = uid in config.ADMIN_USERS

        if not is_admin and not rate_limiter.is_allowed(uid):
            logger.warning(f"Rate limit superado para el usuario {uid}")
            try:
                await update.message.reply_text(
                    "⚠️ Has superado el límite de mensajes permitidos. Por favor, espera unos segundos e intenta nuevamente."
                )
            except Exception:
                pass
            return

        st = state_manager.get_user_state(uid)
        thread_id = get_thread_id(update)

        # Si el usuario estaba esperando búsqueda interactiva
        if st.get("esperando_busqueda"):
            st["esperando_busqueda"] = False  # Consumir estado
            prompt_msg_id = st.pop("search_prompt_msg_id", None)
            if prompt_msg_id:
                try:
                    from services.library_ui import build_search_prompt_rich_blocks
                    from services.rich_message_service import RichMessageService

                    clean_blocks = build_search_prompt_rich_blocks(
                        include_buttons=False, searched_term=text
                    )
                    await RichMessageService.edit_rich_message(
                        chat_id=update.effective_chat.id,
                        message_id=prompt_msg_id,
                        blocks=clean_blocks,
                    )
                except Exception as e:
                    logger.debug(f"No se pudieron quitar los botones del prompt previo: {e}")
                    try:
                        await context.bot.edit_message_reply_markup(
                            chat_id=update.effective_chat.id,
                            message_id=prompt_msg_id,
                            reply_markup=None,
                        )
                    except Exception:
                        pass

            await self.search_h._search_by_term(update, context, text, thread_id)
            return

        # Enviar aviso de "escribiendo..." de Telegram para mejorar la UX
        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="typing",
                message_thread_id=thread_id,
            )
        except Exception:
            pass

        # Recuperar historial previo de chat con IA (últimos turnos)
        history = st.get("ai_history", [])

        # Procesar consulta conversacional sobre la biblioteca con IA
        from services.ai_chat_service import AIChatService

        (
            response_html,
            series_found,
            books_found,
        ) = await AIChatService.process_user_query(
            text, is_admin=is_admin, history=history
        )

        # Guardar en el historial la consulta del usuario y la respuesta de la IA (solo respuestas exitosas, max 10 mensajes)
        if response_html and not response_html.startswith("<i>Lo siento"):
            new_history = list(history)
            new_history.append({"role": "user", "parts": [{"text": text}]})
            new_history.append({"role": "model", "parts": [{"text": response_html}]})
            st["ai_history"] = new_history[-10:]

        # Construir botones interactivos para las recomendaciones encontradas
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        import uuid

        keyboard = []

        # 1. Agregar Series a los botones
        seen_series = set()
        for s in series_found:
            s_id = s.get("id") or s.get("series_hash")
            if not s_id or s_id in seen_series:
                continue
            seen_series.add(s_id)

            s_name = s.get("name") or s.get("series_name") or "Novela"
            # Recortar a 16 caracteres para callback_data
            s_hash_short = s_id[:16]

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"📁 Ver Serie: {s_name}",
                        callback_data=f"show_series|{s_hash_short}",
                    )
                ]
            )

        # 2. Agregar Libros a los botones y registrarlos en el estado
        seen_books = set()
        st["libros"] = st.get("libros", {})
        for b in books_found:
            b_id = b.get("id") or b.get("hash") or b.get("book_hash")
            if not b_id or b_id in seen_books:
                continue
            seen_books.add(b_id)

            b_title = b.get("title") or b.get("filename") or "Libro"
            vol = b.get("volume")
            vol_str = f" Vol. {vol}" if vol is not None else ""

            # Registrar en el estado del usuario para que mostrar_detalles_libro funcione al pulsar
            key = uuid.uuid4().hex[:8]
            st["libros"][key] = {
                "titulo": b_title,
                "autor": b.get("author") or "Desconocido",
                "descarga": b.get("filepath"),
                "portada": b.get("cover_medium")
                or b.get("cover_low")
                or b.get("coverUrl"),
                "hash": b_id,
                "volume": vol,
            }

            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"📕 Ver Libro:{vol_str} {b_title[:25]}...",
                        callback_data=f"lib|{key}",
                    )
                ]
            )

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response_html,
                parse_mode="HTML",
                reply_markup=reply_markup,
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
                    reply_markup=reply_markup,
                    message_thread_id=thread_id,
                )
            except Exception as fe:
                logger.error(f"Error en fallback de mensaje de IA: {fe}")

    async def handle_test_ai(self, update, context):
        """Manejador de depuración para probar la conexión con Gemini en el VPS."""
        uid = update.effective_user.id
        from config.config_settings import config

        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "❌ Este comando es de uso exclusivo para administradores."
            )
            return

        thread_id = get_thread_id(update)
        await update.message.reply_text(
            "🔍 Probando conexión a la API de Gemini desde el servidor...",
            message_thread_id=thread_id,
        )

        try:
            from services.ai_service import AIService

            # Probar llamada
            response = await AIService._call_ai(
                prompt="Responde únicamente con la palabra 'CONEXIÓN_OK'.",
                target_model="gemini-3.1-flash-lite",
                max_retries=1,
            )
            if response:
                await update.message.reply_text(
                    f"✅ Conexión Exitosa con Gemini!\n\n<b>Respuesta:</b> {response}",
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                # Si response es None, hacemos una llamada directa capturando e informando la excepción
                client = AIService._get_client()
                if not client:
                    await update.message.reply_text(
                        "❌ Error: AIService._get_client() retornó None. ¿Está configurada GEMINI_API_KEY en el .env?",
                        message_thread_id=thread_id,
                    )
                    return

                try:
                    from google.genai import types

                    config_args = types.GenerateContentConfig(
                        system_instruction="Test",
                        response_mime_type="text/plain",
                    )
                    res = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents="Test",
                        config=config_args,
                    )
                    await update.message.reply_text(
                        f"❓ Retornó vacio, pero sin excepción. Texto: {res.text if res else 'None'}",
                        message_thread_id=thread_id,
                    )
                except Exception:
                    import traceback

                    tb = traceback.format_exc()
                    await update.message.reply_text(
                        f"❌ Excepción durante la llamada directa:\n\n<code>{tb[:3000]}</code>",
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )

        except Exception:
            import traceback

            tb = traceback.format_exc()
            await update.message.reply_text(
                f"❌ Error al inicializar/probar:\n\n<code>{tb[:3000]}</code>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

    async def handle_setkey(self, update, context):
        """Manejador de administración para actualizar en caliente la API Key de Gemini en el VPS."""
        uid = update.effective_user.id
        from config.config_settings import config

        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "❌ Este comando es de uso exclusivo para administradores."
            )
            return

        thread_id = get_thread_id(update)
        args = context.args
        if not args or len(args) < 1:
            await update.message.reply_text(
                "✏️ Uso: <code>/setkey [nueva_api_key]</code>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        new_key = args[0].strip()
        await update.message.reply_text(
            "⚙️ Actualizando API Key en el servidor VPS...",
            message_thread_id=thread_id,
        )

        try:
            import os

            # 1. Leer y modificar el archivo .env en caliente
            env_path = ".env"
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                key_found = False
                new_lines = []
                for line in lines:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        new_lines.append(f"GEMINI_API_KEY={new_key}\n")
                        key_found = True
                    else:
                        new_lines.append(line)

                if not key_found:
                    new_lines.append(f"\nGEMINI_API_KEY={new_key}\n")

                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            else:
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(f"GEMINI_API_KEY={new_key}\n")

            # 2. Re-cargar en memoria y vaciar cache del cliente
            os.environ["GEMINI_API_KEY"] = new_key
            config._ai_key_logged = False

            from services.ai_service import AIService

            AIService._client = None

            await update.message.reply_text(
                "✅ Archivo .env modificado y cargado en memoria exitosamente.",
                message_thread_id=thread_id,
            )

            # 3. Testear de inmediato
            await update.message.reply_text(
                "🔍 Ejecutando llamada de prueba a Gemini...",
                message_thread_id=thread_id,
            )
            response = await AIService._call_ai(
                prompt="Responde únicamente con la palabra 'OK'.",
                target_model="gemini-3.1-flash-lite",
                max_retries=1,
            )
            if response:
                await update.message.reply_text(
                    f"🚀 Conexión Exitosa con la nueva clave!\n\n<b>Respuesta:</b> {response}",
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                await update.message.reply_text(
                    "❌ La API Key se guardó, pero la llamada a Gemini retornó vacío (None).",
                    message_thread_id=thread_id,
                )

        except Exception:
            import traceback

            tb = traceback.format_exc()
            await update.message.reply_text(
                f"❌ Error al guardar/probar la API Key:\n\n<code>{tb[:3000]}</code>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

    async def handle_catalog_series(self, update, context):
        """Muestra el catálogo interactivo de series en formato Rich Message."""
        from services.library_ui_service import mostrar_series

        await mostrar_series(
            update=update,
            context=context,
            origin_type="all_series",
            page=1,
            force_new=True,
        )

    async def handle_help(self, update, context):
        """Muestra la guía interactiva y comandos en formato Rich Message."""
        from services.library_ui_service import mostrar_ayuda

        await mostrar_ayuda(update=update, context=context, force_new=True)

    async def handle_donations(self, update, context):
        """Muestra las membresías VIP y donaciones en formato Rich Message."""
        from services.library_ui_service import mostrar_donaciones

        await mostrar_donaciones(update=update, context=context, force_new=True)

    async def handle_rules(self, update, context):
        """Muestra las normas de la comunidad en formato Rich Message."""
        from services.library_ui_service import mostrar_reglas

        await mostrar_reglas(update=update, context=context, force_new=True)
