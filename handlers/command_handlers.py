# handlers/command_handlers.py

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from telegram.ext import ContextTypes, CommandHandler
from core.state_manager import state_manager
from utils.download_limiter import downloads_left, record_download, can_download
from services.opds_service import mostrar_colecciones, get_cached_feed
from config.config_settings import config
from utils.helpers import get_thread_id, is_command_for_bot, build_search_url
# from utils.http_client import parse_feed_from_url  <-- Removing this
from utils.decorators import rate_limit

logger = logging.getLogger(__name__)


class CommandHandlers:
    def __init__(self, app):
        self.app = app
        from services.settings_service import SettingsService

        self.settings_service = SettingsService()

        # Registrar handlers existentes
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("start", self.start))

        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("cancel", self.cancel))
        app.add_handler(CommandHandler("plugins", self.plugins))
        app.add_handler(CommandHandler("evil", self.evil))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start: inicializa estado; admin->evil, otros->normal."""

        uid = update.effective_user.id
        left = await downloads_left(uid)

        text = (
            "👋 ¡Hola! Comencemos.\n\n✅ Tienes descargas ilimitadas."
            if left == "ilimitadas"
            else f"👋 ¡Hola! Comencemos.\n\n⚡️ Te quedan {left} descargas hoy."
        )

        # Capturar message_thread_id para soporte de topics
        thread_id = get_thread_id(update)

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=text, message_thread_id=thread_id
        )

        st = state_manager.get_user_state(uid)
        # Limpiar estado temporal de libro anterior al reiniciar
        for k in (
            "epub_buffer",
            "meta_pendiente",
            "portada_pendiente",
            "titulo_pendiente",
            "fb_caption",
        ):
            st.pop(k, None)
        st["destino"] = update.effective_chat.id
        st["chat_origen"] = update.effective_chat.id
        st["message_thread_id"] = thread_id

        # Publishers (ephemeral choice for next book). Admin-only users (not publishers)
        # will be handled separately (go directly to Evil). For users that are both
        # admin+publisher we still show the ephemeral choice here.
        if uid in config.FACEBOOK_PUBLISHERS:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "📨 Publicar en Telegram (próximo libro)",
                        callback_data="set_publish_temp|telegram",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 Publicar en Facebook (próximo libro)",
                        callback_data="set_publish_temp|facebook",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⛔ Omitir", callback_data="set_publish_temp|none"
                    )
                ],
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔧 Eres publisher — ¿dónde quieres publicar la próxima vez que selecciones un libro?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=thread_id,
            )
            # When a publisher sees this choice we must not continue to show
            # the collections menu until they choose where to publish. Defer
            # showing collections until the selection callback runs.
            return

        # Administradores: mostrar selección de destino Evil directamente
        # NOTE: If a user is both admin and publisher we *do not* show the
        # destination menu here. For admin+publisher the ephemeral publish
        # choice shown above will decide whether to show the destination
        # selection (Telegram) or assume "aquí" (Facebook). If the user is an
        # admin but *not* a publisher, we show the Evil menu immediately.
        if uid in config.ADMIN_USERS and uid not in config.FACEBOOK_PUBLISHERS:
            # Administradores entran directamente en el menú Evil (sin contraseña)
            if uid in config.ADMIN_USERS:
                root = config.OPDS_ROOT_EVIL
                st["opds_root"] = root
                st["opds_root_base"] = root
                st["historial"] = []
                st["ultima_pagina"] = root
            # Mostrar opciones de destino
            keyboard = [
                [InlineKeyboardButton("📍 Aquí", callback_data="destino|aqui")],
                [
                    InlineKeyboardButton(
                        "📣 BotTest", callback_data="destino|@ZeePubBotTest"
                    )
                ],
                [InlineKeyboardButton("📣 ZeePubs", callback_data="destino|@ZeePubs")],
                [InlineKeyboardButton("✏️ Otro", callback_data="destino|otro")],
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔧 Modo Evil: ¿Dónde quieres publicar?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=thread_id,
            )
            return

        # (publisher prompt shown above; continue)

        # Usuarios normales
        root = config.OPDS_ROOT_START
        st["opds_root"] = root
        st["opds_root_base"] = root
        st["historial"] = []
        st["ultima_pagina"] = root
        await mostrar_colecciones(
            update, context, root, from_collection=False, new_message=True
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status: informa estado interno, nivel de usuario y descargas restantes."""
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        # Obtener info extendida
        from services.user_service import get_effective_user

        user_data = await get_effective_user(uid)

        roles_display = {
            "admin": "Admin 🛠️",
            "staff": "Staff 🛡️",
            "premium": "Premium ✨",
            "vip": "VIP ⭐️",
            "white": "Patrocinador 🤍",
            "free": "Lector 📚",
        }

        role_key = user_data.get("role", "free")
        status_label = user_data.get("status_label")
        expires_at = user_data.get("expires_at")

        # Override label if custom status exists
        user_level = (
            status_label if status_label else roles_display.get(role_key, "Lector")
        )

        if role_key == "banned":
            user_level = "🚫 Baneado"

        # Max dl logic
        if role_key in ("admin", "staff", "premium", "banned"):
            max_dl = None
        elif role_key == "vip":
            max_dl = config.VIP_DOWNLOADS_PER_DAY
        elif role_key == "white":
            max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
        else:
            max_dl = config.MAX_DOWNLOADS_PER_DAY

        # Descargas usadas y restantes
        used = st.get("downloads_used", 0)

        if max_dl is None:
            if role_key == "banned":
                left_text = "⛔ Acceso denegado"
            else:
                left_text = "✅ Descargas ilimitadas"
        else:
            remaining = max_dl - used
            left_text = f"⚡️ Te quedan {remaining if remaining>0 else 0} descargas por día (de {max_dl}) [Usadas: {used}]"

        # Calcular tiempo para próximo reset
        from datetime import datetime, timedelta

        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        time_left = next_midnight - now
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        user_name = update.effective_user.first_name.replace("<", "&lt;").replace(
            ">", "&gt;"
        )

        from utils.helpers import get_version_string

        version = get_version_string()

        text = (
            f"🤖 <b>ZeePub Bot</b> v{version}\n\n"
            "📊 <b>Tu Estado</b>\n\n"
            f"👤 <b>Usuario:</b> {user_name}\n"
            f"🆔 <b>ID:</b> {uid}\n"
            f"⭐ <b>Nivel:</b> {user_level}\n"
        )

        if expires_at:
            if role_key == "banned":
                text += f"📅 <b>Castigo hasta:</b> {expires_at.strftime('%d/%m/%Y %H:%M')}\n"
            else:
                text += f"📅 <b>Vence:</b> {expires_at.strftime('%d/%m/%Y')}\n"

        text += f"📉 <b>Descargas:</b> {left_text}\n"

        # Solo mostrar reinicio si NO es ilimitado y NO está baneado
        if max_dl is not None:
            text += f"⏳ <b>Reinicio en:</b> {hours}h {minutes}m\n"

        thread_id = get_thread_id(update)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel: limpia estado, borra menús y confirma cancelación."""
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        # Limpiar estado
        st.pop("esperando_busqueda", None)
        st.pop("esperando_destino_manual", None)
        st.pop("series_id", None)
        st.pop("volume_id", None)

        chat_id = update.effective_chat.id
        msg_id = update.message.message_id

        # Borrar el último mensaje anterior (el menú)
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=msg_id - 1)
        except Exception:
            logger.debug("No se pudo borrar mensaje anterior")

        # Borrar el mensaje de /cancel
        try:
            await update.message.delete()
        except Exception:
            logger.debug("No se pudo borrar comando /cancel")

        thread_id = get_thread_id(update)
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ ¡Entendido! Operación cancelada.",
            message_thread_id=thread_id,
        )

    async def plugins(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /plugins: lista plugins activos."""
        pm = getattr(self.app, "plugin_manager", None)
        if not pm:
            thread_id = get_thread_id(update)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Sistema de plugins no disponible.",
                message_thread_id=thread_id,
            )
            return
        plugins = pm.list_plugins()
        if not plugins:
            thread_id = get_thread_id(update)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="📦 No hay plugins activos.",
                message_thread_id=thread_id,
            )
            return
        text = "🔌 <b>Plugins activos:</b>\n\n"
        for name, info in plugins.items():
            safe_name = name.replace("<", "&lt;").replace(">", "&gt;")
            safe_desc = info["description"].replace("<", "&lt;").replace(">", "&gt;")
            text += f"• <b>{safe_name}</b> v{info['version']} — <i>{safe_desc}</i>\n"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=text, parse_mode="HTML"
        )

    async def evil(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /evil: inicia modo privado solicitando contraseña."""
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        st["opds_root"] = config.OPDS_ROOT_EVIL
        st["historial"] = []
        st["esperando_password"] = True
        thread_id = get_thread_id(update)
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔒 Modo Privado. Por favor, ingresa la contraseña:",
            message_thread_id=thread_id,
        )
        st["msg_esperando_pwd"] = message.message_id

    @rate_limit("search", max_requests=30, window_seconds=60)
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search: busca EPUB con término inline o pide uno."""
        # En grupos con múltiples bots, ignorar si el comando no es para este bot
        bot_username = context.bot.username
        if not is_command_for_bot(update, bot_username):
            return
        # Check User Role
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        thread_id = get_thread_id(update)
        st["message_thread_id"] = thread_id  # Guardar para respuestas

        # Check ban status
        from services.user_service import get_effective_user

        user_info = await get_effective_user(uid)
        if user_info.get("role") == "banned":
            expires_at = user_info.get("expires_at")
            msg = "⛔ Estás <b>baneado</b> del bot."
            if expires_at:
                msg += f" Hasta: <b>{expires_at.strftime('%Y-%m-%d %H:%M')}</b>"
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        # Verificar si hay término de búsqueda en el comando
        if context.args:
            # Hay término: /search harry potter
            termino = " ".join(context.args).strip()
            logger.debug(f"Usuario {uid} buscando con /search: {termino}")

            search_url = build_search_url(termino, uid)
            logger.debug(f"URL de búsqueda: {search_url}")
            feed = await get_cached_feed(search_url)

            if not feed or not getattr(feed, "entries", []):
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "🔄 Volver a buscar", callback_data="buscar"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📚 Ir a colecciones", callback_data="volver_colecciones"
                        )
                    ],
                ]
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"🔍 Mmm, no encontré nada para: {termino}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    message_thread_id=thread_id,
                )
            else:
                logger.debug(f"Encontrados {len(feed.entries)} resultados")
                # Asegurar que los resultados aparezcan en el chat actual
                st["destino"] = update.effective_chat.id
                st["chat_origen"] = update.effective_chat.id
                await mostrar_colecciones(
                    update, context, search_url, from_collection=False, new_message=True
                )
        else:
            # Sin término: pedir uno
            st["esperando_busqueda"] = True
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔍 ¿Qué libro buscas? Escribe el título o autor:",
                message_thread_id=thread_id,
            )
