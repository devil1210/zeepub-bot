# handlers/command_handlers.py

import logging
import os
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
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

        first_name = update.effective_user.first_name

        # Template System
        cms = context.application.plugin_manager.get_plugin("custom_messages")

        # Ya no usamos deep links con parámetros - el estado se maneja proactivamente

        if left == "ilimitadas":
            text = (
                await cms.get_text("start_welcome_unlimited", Nombre=update.effective_user.mention_html())
                if (cms and cms.enabled)
                else "👋 ¡Hola {first_name}! Comencemos.\n\n✅ Tienes descargas ilimitadas.".replace(
                    "{first_name}", first_name
                )
            )
        else:
            text = (
                await cms.get_text(
                    "start_welcome_limited",
                    Nombre=update.effective_user.mention_html(),
                    Descargas=left,
                )
                if (cms and cms.enabled)
                else f"👋 ¡Hola {first_name}! Comencemos.\n\n⚡️ Te quedan {left} descargas hoy."
            )

        # Capturar message_thread_id para soporte de topics
        thread_id = get_thread_id(update)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            message_thread_id=thread_id,
            parse_mode=ParseMode.HTML,
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
        # Helper: Determine if user is a Publisher
        # Logic: Nivel Staff AND Rol Publicador
        from services.user_service import get_effective_user
        user_data_start = await get_effective_user(uid)
        role_start = user_data_start.get("role", "free")
        custom_status_start = user_data_start.get("custom_status")

        is_publisher = (role_start == "staff" and custom_status_start == "Publicador")

        # Legacy fallback or Override: Check config list too?
        # User said "para esta nueva combinacion es...", implying strict definition.
        # But let's keep config list as "Super Publishers" just in case, or stick to strict req.
        # Sticking to strict requirement per user instruction.
        # Publishers (ephemeral choice for next book). Admin-only users (not publishers)
        # will be handled separately (go directly to Evil). For users that are both
        # admin+publisher we still show the ephemeral choice here.
        if is_publisher:
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
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_txt = "🔧 Eres publisher — ¿dónde quieres publicar la próxima vez que selecciones un libro?"
            text_pub = (
                await cms.get_text("publisher_target_prompt")
                if (cms and cms.enabled)
                else base_txt
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_pub,
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
        if uid in config.ADMIN_USERS and not is_publisher:
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

            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_txt = "🔧 Modo Evil: ¿Dónde quieres publicar?"
            text_evil = (
                await cms.get_text("evil_mode_prompt") if (cms and cms.enabled) else base_txt
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_evil,
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML,
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

        # Custom Status (Apodo/Label) logic
        # Nivel = System Role (Admin, Staff, etc.)
        # Rol = Custom Label (Maquetador, etc)

        system_role_text = roles_display.get(role_key, "Lector")
        if role_key == "banned":
            system_role_text = "🚫 Baneado"

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

        if expires_at:
            fmt = "%d/%m/%Y %H:%M" if role_key == "banned" else "%d/%m/%Y"
            label = "Castigo hasta" if role_key == "banned" else "Vence"
            expires_str = expires_at.strftime(fmt)
        else:
            expires_str = None  # Ensure it is None so {{if}} sees it as False

        # Reset Time logic
        reset_time_str = None
        if max_dl is not None:
            reset_time_str = f"{hours}h {minutes}m"

        # Build default text structure for fallback with Conditional Syntax
        base_text = (
            f"🤖 <b>ZeePub Bot</b> {version}\n\n"
            "📊 <b>Tu Estado</b>\n\n"
            f"👤 <b>Usuario:</b> [Nombre]\n"
            f"🆔 <b>ID:</b> [ID]\n"
            f"⭐ <b>Nivel:</b> [Nivel]\n"
            "{{if Expires}}📅 <b>Vence:</b> [Expires]\n{{endif}}"
            f"📉 <b>Descargas:</b> [Descargas]\n"
            "{{if ResetTime}}⏳ <b>Reinicio en:</b> [ResetTime]\n{{endif}}"
        )

        cms = context.application.plugin_manager.get_plugin("custom_messages")

        final_text = base_text
        if cms and cms.enabled:
            # Pass explicit variables to override any global default logic
            # Nivel: System Role (Staff, Admin, VIP)
            # Rol: Custom Label (Maquetador, etc) -> Only explicit if exists, else same as Nivel/Empty?
            # Let's fallback to system role if status_label is empty, so [Rol] isn't empty.
            rol_val = status_label if status_label else system_role_text

            final_text = await cms.get_text(
                "status_message",
                user=update.effective_user,
                Nivel=system_role_text,
                Rol=rol_val, 
                Descargas=left_text,
                ResetTime=reset_time_str,
                Expires=expires_str,
            )

        thread_id = get_thread_id(update)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=final_text,
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

        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_cancel = "✅ ¡Entendido! Operación cancelada."
        text_cancel = (
            await cms.get_text(
                "cancel_confirmation",
                user=update.effective_user,
            )
            if (cms and cms.enabled)
            else base_cancel
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text=text_cancel,
            message_thread_id=thread_id,
            parse_mode=ParseMode.HTML,
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
        st["historial"] = []
        st["esperando_password"] = True
        thread_id = get_thread_id(update)

        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_pwd = "🔒 Modo Privado. Por favor, ingresa la contraseña:"
        text_pwd = (
            cms.get_text("evil_password_prompt") if (cms and cms.enabled) else base_pwd
        )

        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text_pwd,
            message_thread_id=thread_id,
            parse_mode=ParseMode.HTML,
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

            cms = context.application.plugin_manager.get_plugin("custom_messages")
            default_msg = "⛔ Estás <b>baneado</b> del bot."
            if expires_at:
                default_msg += f" Hasta: <b>{expires_at.strftime('%Y-%m-%d %H:%M')}</b>"

            msg = default_msg
            if cms and cms.enabled:
                exp_str = (
                    expires_at.strftime("%Y-%m-%d %H:%M")
                    if expires_at
                    else "Indefinido"
                )
                msg = cms.get_text("banned_message", Fecha=exp_str)

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

                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_no = f"🔍 Mmm, no encontré nada para: {termino}"

                safe_term = html.escape(termino)
                text_no = base_no
                if cms and cms.enabled:
                    text_no = cms.get_text(
                        "search_no_results",
                        Termino=safe_term,
                    )

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text_no,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    message_thread_id=thread_id,
                    parse_mode=ParseMode.HTML,
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
            st["esperando_busqueda"] = True
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_search = "🔍 ¿Qué libro buscas? Escribe el título o autor:"
            text_search = (
                await cms.get_text("search_prompt")
                if (cms and cms.enabled)
                else base_search
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_search,
                message_thread_id=thread_id,
            )
