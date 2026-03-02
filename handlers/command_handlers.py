# handlers/command_handlers.py

import logging
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.library_ui_service import mostrar_menu_principal
from services.user_service import get_effective_user

# from utils.http_client import parse_feed_from_url  <-- Removing this
from utils.decorators import rate_limit
from utils.download_limiter import downloads_left
from utils.helpers import get_thread_id, is_command_for_bot

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
        app.add_handler(CommandHandler("changeweb", self.changeweb))
        app.add_handler(CommandHandler("acceso_web", self.acceso_web))
        app.add_handler(CommandHandler("web_login", self.acceso_web))

        # Nuevos handlers para catálogo
        app.add_handler(CommandHandler("catalog", self.catalog))
        app.add_handler(CommandHandler("catalogo", self.catalog))

    @rate_limit("catalog", max_requests=5, window_seconds=60)
    async def catalog(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /catalog: Muestra el catálogo principal."""
        from services.library_ui_service import mostrar_menu_principal

        # Opcional: limpiar mensajes innecesarios si es en privado
        if update.message and update.effective_chat.type == "private":
            try:
                await update.message.delete()
            except Exception:
                pass

        await mostrar_menu_principal(update, context)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start: inicializa estado; admin->evil, otros->normal."""

        uid = update.effective_user.id

        # Auto-sincronizar desde ENV (ADMIN_USERS, VIP_LIST, etc.)
        from services.user_service import sync_user_from_env

        try:
            await sync_user_from_env(uid, tg_user=update.effective_user)
        except Exception as e:
            logger.error(f"Error syncing user {uid} from ENV: {e}")

        left = await downloads_left(uid, tg_user=update.effective_user)

        first_name = update.effective_user.first_name

        # Template System
        cms = context.application.plugin_manager.get_plugin("custom_messages")

        # Ya no usamos deep links con parámetros - el estado se maneja proactivamente

        if left == "ilimitadas":
            text = (
                await cms.get_text("start_welcome_unlimited", user=update.effective_user)
                if (cms and cms.enabled)
                else "👋 ¡Hola {first_name}! Comencemos.\n\n✅ Tienes descargas ilimitadas.".replace(
                    "{first_name}", first_name
                )
            )
        else:
            text = (
                await cms.get_text(
                    "start_welcome_limited",
                    user=update.effective_user,
                    Descargas=left,
                )
                if (cms and cms.enabled)
                else f"👋 ¡Hola {first_name}! Comencemos.\n\n⚡️ Te quedan {left} descargas hoy."
            )

        # Capturar message_thread_id para soporte de topics
        thread_id = get_thread_id(update)

        # API 9.3: Soporte para tópicos en chat privado
        bot_user_dict = update.effective_user.to_dict()
        has_topics = bot_user_dict.get("has_topics_enabled", False)

        if has_topics:
            from services.topic_service import topic_service

            # Asegurar que los tópicos existan y obtener el ID del tópico "Sistema" para la bienvenida
            topic_ids = await topic_service.ensure_topics(context.bot, uid)
            if topic_ids:
                # Si hay tópicos, redirigimos el mensaje de bienvenida al tópico "Sistema"
                thread_id = topic_ids.get("sistema", thread_id)

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
        # 1. Definir Nivel y Rol prioritario
        user_info = await get_effective_user(uid, tg_user=update.effective_user)
        level_start = user_info.get("level", "free")
        role_start = user_info.get("role")
        is_admin = uid in config.ADMIN_USERS
        is_publisher = level_start == "staff" and role_start == "Publicador"

        # 2. Lógica de Menús (Jerarquía: Admin > Publisher > User)
        if is_admin and not is_publisher:
            # Administradores puros: Menú Evil directo
            st["historial"] = []
            st["ultima_pagina"] = config.BASE_URL

            from repositories.publication_repository import PublicationRepository

            pub_repo = PublicationRepository()
            active_channels = await pub_repo.get_channels(active_only=True)

            keyboard = [[InlineKeyboardButton("📍 Aquí", callback_data="destino|aqui")]]

            # Insert dynamic channels
            for ch in active_channels:
                prefix = "📣 " if ch.type == "telegram" else "📘 " if ch.type == "facebook" else "🌐 "
                btn_text = f"{prefix}{ch.name}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"destino|{ch.chat_id_or_username}")])

            keyboard.append([InlineKeyboardButton("✏️ Otro", callback_data="destino|otro")])

            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_txt = "🔧 Modo Evil: ¿Dónde quieres publicar?"
            text_evil = await cms.get_text("evil_mode_prompt") if (cms and cms.enabled) else base_txt

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_evil,
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=thread_id,
                parse_mode=ParseMode.HTML,
            )
            return

        if is_publisher:
            # Publishers: Selector de destino efímero
            keyboard = [
                [InlineKeyboardButton("📨 Publicar en Telegram", callback_data="set_publish_temp|telegram")],
                [InlineKeyboardButton("📝 Publicar en Facebook", callback_data="set_publish_temp|facebook")],
                [InlineKeyboardButton("⛔ Omitir", callback_data="set_publish_temp|none")],
            ]
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_txt = "🔧 Eres publisher — ¿dónde quieres publicar la próxima vez?"
            text_pub = await cms.get_text("publisher_target_prompt") if (cms and cms.enabled) else base_txt
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_pub,
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=thread_id,
            )
            return

        # (publisher prompt shown above; continue)

        # Usuarios normales: ir directamente a la Biblioteca Local
        st["historial"] = []
        await mostrar_menu_principal(update, context)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status: informa estado interno, nivel de usuario y descargas restantes."""
        uid = update.effective_user.id
        target_user = update.effective_user

        # Lógica para administradores: si citan un mensaje, mostrar status de ese usuario
        if update.message.reply_to_message:
            if uid in config.ADMIN_USERS:
                target_user = update.message.reply_to_message.from_user
                uid = target_user.id
                logger.info(f"Admin {update.effective_user.id} requested status for user {uid}")

        st = state_manager.get_user_state(uid)

        # Obtener info extendida
        from services.user_service import get_effective_user

        user_data = await get_effective_user(uid, tg_user=target_user)

        roles_display = {
            "admin": "Admin 🛠️",
            "staff": "Staff 🛡️",
            "premium": "Premium ✨",
            "vip": "VIP ⭐️",
            "white": "Patrocinador 🤍",
            "free": "Lector 📚",
        }

        level_key = user_data.get("level", "free")
        user_data.get("role")
        status_label = user_data.get("status_label")
        expires_at = user_data.get("expires_at")

        # Custom Status (Apodo/Label) logic
        # Nivel = System Role (Admin, Staff, etc.)
        # Rol = Custom Label (Maquetador, etc)

        system_role_text = roles_display.get(level_key, "Lector")
        if level_key == "banned":
            system_role_text = "🚫 Baneado"

        # Max dl logic
        if level_key in ("admin", "staff", "premium", "banned"):
            max_dl = None
        elif level_key == "vip":
            max_dl = config.VIP_DOWNLOADS_PER_DAY
        elif level_key == "white":
            max_dl = config.WHITELIST_DOWNLOADS_PER_DAY
        else:
            max_dl = config.MAX_DOWNLOADS_PER_DAY

        # Descargas usadas y restantes
        used = st.get("downloads_used", 0)

        if max_dl is None:
            if level_key == "banned":
                left_text = "⛔ Acceso denegado"
            else:
                left_text = "✅ Descargas ilimitadas"
        else:
            remaining = max_dl - used
            left_text = (
                f"⚡️ Te quedan {remaining if remaining > 0 else 0} descargas por día (de {max_dl}) [Usadas: {used}]"
            )

        # Calcular tiempo para próximo reset

        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        time_left = next_midnight - now
        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)

        update.effective_user.first_name.replace("<", "&lt;").replace(">", "&gt;")

        from utils.helpers import get_version_string

        version = get_version_string()

        if expires_at:
            fmt = "%d/%m/%Y %H:%M" if level_key == "banned" else "%d/%m/%Y"
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
            total_dl = user_data.get("total_downloads", 0)

            final_text = await cms.get_text(
                "status_message",
                user=target_user,
                Nivel=system_role_text,
                Rol=rol_val,
                Descargas=left_text,
                TotalDescargas=str(total_dl),
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode="HTML")

    async def evil(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /evil: inicia modo privado solicitando contraseña."""
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        st["historial"] = []
        st["esperando_password"] = True
        st["historial"] = []
        st["esperando_password"] = True
        thread_id = get_thread_id(update)

        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_pwd = "🔒 Modo Privado. Por favor, ingresa la contraseña:"
        text_pwd = cms.get_text("evil_password_prompt") if (cms and cms.enabled) else base_pwd

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
        if user_info.get("level") == "banned":
            expires_at = user_info.get("expires_at")

            cms = context.application.plugin_manager.get_plugin("custom_messages")
            default_msg = "⛔ Estás <b>baneado</b> del bot."
            if expires_at:
                default_msg += f" Hasta: <b>{expires_at.strftime('%Y-%m-%d %H:%M')}</b>"

            msg = default_msg
            if cms and cms.enabled:
                exp_str = expires_at.strftime("%Y-%m-%d %H:%M") if expires_at else "Indefinido"
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

            from services.library_service import LibraryService
            from services.library_ui_service import mostrar_resultados_locales

            # 1. Búsqueda de Series (Agrupada)
            res_series = await LibraryService.search_series(termino, items_per_page=30)
            series_list = res_series.get("items", [])
            series_hashes = {s["series_hash"] for s in series_list}

            # 2. Búsqueda de Libros Individuales
            res_books = await LibraryService.search_books(termino)
            all_books = res_books.get("results", [])

            # Filtramos libros que YA pertenecen a las series encontradas
            books_standalone = [b for b in all_books if b.get("series_hash") not in series_hashes]

            await mostrar_resultados_locales(update, context, termino, series_list, books_standalone)
            return
        else:
            st["esperando_busqueda"] = True
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_search = "🔍 ¿Qué libro buscas? Escribe el título o autor:"
            text_search = await cms.get_text("search_prompt") if (cms and cms.enabled) else base_search
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_search,
                message_thread_id=thread_id,
            )

    async def changeweb(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /changeweb: Cambia entre la interfaz nueva (web_client) y la antigua (zeepub-web)."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        # Verificar permisos de admin
        if uid not in config.ADMIN_USERS:
            return  # Silencioso para no admins

        if not context.args:
            current = "Desconocido"
            import os

            # Intentar leer del .env directamente para mostrar lo real
            try:
                with open(".env") as f:
                    for line in f:
                        if line.startswith("WEB_CLIENT_DIR="):
                            current = line.split("=")[1].strip()
            except Exception:
                current = os.getenv("WEB_CLIENT_DIR", "web_client (default)")

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔧 <b>Configuración Actual:</b> <code>{current}</code>\n\nUsa: <code>/changeweb new</code> o <code>/changeweb old</code>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        target = context.args[0].lower()
        new_val = ""
        if target in ["new", "nuevo", "moderno"]:
            new_val = "web_client"
        elif target in ["old", "viejo", "legacy"]:
            new_val = "zeepub-web"
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Opción no válida. Usa 'new' o 'old'.",
                message_thread_id=thread_id,
            )
            return

        # Delegar actualización segura al SettingsService
        try:
            success = await self.settings_service.update_env_variable("WEB_CLIENT_DIR", new_val)
            if success:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ Configuración actualizada a: <code>{new_val}</code>\n\n🔄 Reiniciando bot para aplicar cambios...",
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )

                import sys
                import time

                # Salida controlada
                time.sleep(1.5)
                sys.exit(0)
            else:
                raise ValueError("No se pudo actualizar el archivo .env")
        except Exception as e:
            logger.error(f"Error en /changeweb: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error al actualizar configuración: {e}",
                message_thread_id=thread_id,
            )

    async def acceso_web(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera un enlace de acceso mágico para la web."""
        uid = update.effective_user.id
        from services.user_service import get_effective_user

        user_info = await get_effective_user(uid)
        email = user_info.get("email")

        if not email:
            # Pedir email
            st = state_manager.get_user_state(uid)
            st["esperando_email"] = True
            await update.message.reply_html(
                "📧 <b>Acceso Web</b>\n\nPara vincular tu cuenta con la web, necesito tu correo electrónico.\n\nPor favor, escribe tu email a continuación:"
            )
            return

        # Generar Magic Link vía Supabase Admin
        from core.supabase_manager import supabase_manager

        if not supabase_manager.is_active:
            await update.message.reply_html(
                "❌ <b>Servidor No Configurado</b>\n\nEl servicio de autenticación Supabase no está activo. "
                "Contacta con un administrador."
            )
            return

        try:
            client = supabase_manager.get_client()

            # 1. Validar WEBAPP_URL
            redirect_url = config.WEBAPP_URL
            if not redirect_url or "localhost" in redirect_url and not config.DEBUG:
                logger.warning(f"WEBAPP_URL potencialmente inválido: {redirect_url}")

            if not redirect_url.startswith("http"):
                redirect_url = f"https://{redirect_url}"

            # 2. Intentar generar link
            res = client.auth.admin.generate_link(
                {"type": "magiclink", "email": email, "options": {"redirectTo": redirect_url}}
            )

            if not res or not hasattr(res, "properties") or not res.properties.action_link:
                error_msg = getattr(res, "error", "Error desconocido en Supabase")
                raise ValueError(f"Fallo al generar enlace: {error_msg}")

            link = res.properties.action_link

            await update.message.reply_html(
                f"🔗 <b>¡Listo, {update.effective_user.first_name}!</b>\n\n"
                f"Usa este enlace para entrar sin contraseña (válido 1h):\n\n"
                f"<a href='{link}'>🚀 Acceder a ZeePub Web</a>\n\n"
                f"<i>Nota: Este enlace es personal y vincula tu cuenta de Telegram ({uid}).</i>"
            )
        except Exception as e:
            logger.error(f"Error en /acceso_web para {uid}: {e}")
            await update.message.reply_html(
                "❌ <b>Error de Autenticación</b>\n\n"
                "No pudimos generar tu acceso. Posibles causas:\n"
                "• El correo no está registrado en el sistema.\n"
                "• Error de conexión con Supabase.\n"
                "• Configuración de URL desactualizada.\n\n"
                "<i>Reintenta en unos minutos o usa /start para refrescar tu sesión.</i>"
            )
