# handlers/command_handlers.py

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from telegram.ext import ContextTypes, CommandHandler
from core.state_manager import state_manager
from utils.download_limiter import downloads_left, record_download, can_download
from services.opds_service import mostrar_colecciones
from config.config_settings import config
from utils.helpers import get_thread_id, is_command_for_bot, build_search_url
from utils.http_client import parse_feed_from_url

logger = logging.getLogger(__name__)


class CommandHandlers:
    def __init__(self, app):
        self.app = app
        from services.settings_service import SettingsService

        self.settings_service = SettingsService()

        # Registrar handlers existentes
        app.add_handler(CommandHandler("search", self.search))
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("cancel", self.cancel))
        app.add_handler(CommandHandler("plugins", self.plugins))
        app.add_handler(CommandHandler("evil", self.evil))
        # Registrar /reset
        app.add_handler(CommandHandler("reset", self.reset_command))

        # Registrar comandos de gestión de usuarios (admin)
        app.add_handler(CommandHandler("add_user", self.add_user))
        app.add_handler(CommandHandler("remove_user", self.remove_user))
        app.add_handler(CommandHandler("set_staff_status", self.set_staff_status))

        # Registrar /id (admin only)
        app.add_handler(CommandHandler("id", self.get_id))

        # Registrar /stats (admin only)
        app.add_handler(CommandHandler("stats", self.stats))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start: inicializa estado; admin->evil, otros->normal."""

        uid = update.effective_user.id
        left = downloads_left(uid)

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

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help: muestra ayuda dinámica y paginada."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        # Importar lógica compartida para evitar duplicación
        # (Importación local para evitar ciclos y errores de carga inicial)
        from handlers.callback_handlers import _get_help_data, _get_help_keyboard

        help_data, is_admin, is_publisher = _get_help_data(uid)

        # Mostrar categoría "home" por defecto
        cat_title, commands = help_data.get("home", ("Inicio", []))

        text = f"🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
        text += f"📂 <b>Categoría: {cat_title}</b>\n\n"

        for cmd, desc in commands:
            safe_cmd = cmd.replace("<", "&lt;").replace(">", "&gt;")
            safe_desc = desc.replace("<", "&lt;").replace(">", "&gt;")
            text += f"<b>{safe_cmd}</b>\n   ╰ {safe_desc}\n"

        # Teclado dinámico
        keyboard = _get_help_keyboard(is_admin, is_publisher)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            reply_markup=keyboard,
            message_thread_id=thread_id,
        )

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /stats: muestra estadísticas.
        Uso:
        - /stats: Resumen diario (usuarios activos, descargas, roles).
        - /stats <rol>: Lista usuarios en base de datos con ese rol.
        """
        uid = update.effective_user.id
        # Verificar permisos (Admin o Staff)
        from services.user_service import get_effective_user

        user_info = get_effective_user(uid)
        role = user_info.get("role", "free")
        is_admin = role == "admin" or uid in config.ADMIN_USERS
        if not is_admin and role != "staff":
            return

        thread_id = get_thread_id(update)

        # Modo Listar Usuarios por Rol: /stats premium
        if context.args:
            target_role = context.args[0].lower()
            from services.user_service import get_users_by_role

            users_list = get_users_by_role(target_role)

            if not users_list:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"ℹ️ No se encontraron usuarios con el rol <b>{target_role}</b> en base de datos.",
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
                return

            msg = f"📋 <b>Usuarios con rol: {target_role.capitalize()}</b> ({len(users_list)})\n\n"
            count = 0
            for u in users_list:
                count += 1
                if count > 50:
                    msg += f"... y otros {len(users_list) - 50} más."
                    break

                u_id = u["telegram_id"]
                expires = u.get("expires_at")

                exp_str = "Infinito"
                if expires:
                    from datetime import datetime

                    # Calcular días restantes
                    now = datetime.utcnow()
                    if isinstance(expires, str):
                        try:
                            from dateutil import parser

                            expires = parser.parse(expires)
                        except Exception:
                            pass

                    if hasattr(expires, "date"):
                        delta = expires - now
                        days_left = delta.days
                        if days_left < 0:
                            exp_str = "Vencido"
                        else:
                            exp_str = f"{days_left} días"

                msg += f"👤 <code>{u_id}</code> | ⏳ {exp_str}\n"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

        # Modo Resumen Diario
        from services.stats_service import get_daily_stats

        data = get_daily_stats()

        # Formatear desglose por roles
        by_role = data.get("by_role", {})
        roles_txt = ""
        if by_role:
            roles_txt = "\n🏷️ <b>Por Nivel (Activos):</b>\n"
            for r, count in by_role.items():
                roles_txt += f"  • {r.capitalize()}: {count}\n"

        text = (
            "📊 <b>Estadísticas Diarias (Hoy)</b>\n\n"
            f"👥 <b>Usuarios Únicos:</b> {data['unique_users']}\n"
            f"⬇️ <b>Descargas Totales:</b> {data['total_downloads']}\n"
            f"{roles_txt}"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status: informa estado interno, nivel de usuario y descargas restantes."""
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        # Obtener info extendida
        from services.user_service import get_effective_user

        user_data = get_effective_user(uid)

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

        user_info = get_effective_user(uid)
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
            feed = await parse_feed_from_url(search_url)

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

    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /add_user <id> <rol> [meses]
        Agrega un usuario con un rol específico y duración opcional.
        """
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: /add_user <id> <rol> [meses]\n"
                "Roles: white, vip, premium, staff\n"
                "Ejemplo: /add_user 123456789 vip 6"
            )
            return

        target_id_str = context.args[0]
        role = context.args[1].lower()

        if not target_id_str.isdigit():
            await update.message.reply_text("❌ ID inválido.")
            return
        target_id = int(target_id_str)

        valid_roles = ["white", "vip", "premium", "staff", "banned"]
        if role not in valid_roles:
            await update.message.reply_text(
                f"❌ Rol inválido. Use: {', '.join(valid_roles)}"
            )
            return

        # Determine duration
        duration = None
        duration_days = None

        if len(context.args) >= 3:
            if context.args[2].isdigit():
                val = int(context.args[2])
                # If role is banned, treat duration as days
                if role == "banned":
                    duration_days = val
                else:
                    duration = val
        else:
            # Use default from settings if not provided
            # Only for non-staff roles usually, but consistent behavior is better
            if role != "staff" and role != "banned":
                from services.settings_service import get_setting

                duration = int(get_setting("benefit_duration_months", "6"))

        from services.user_service import upsert_user

        upsert_user(
            target_id,
            role,
            duration_months=duration,
            created_by=uid,
            duration_days=duration_days,
        )

        msg = f"✅ Usuario <code>{target_id}</code> agregado como <b>{role.capitalize()}</b>"
        if duration_days:
            msg += f" por <b>{duration_days} días</b> (Baneado)."
        elif duration:
            msg += f" por <b>{duration} meses</b>."
        else:
            msg += " (Permanente/Hasta cancelación)."

        await update.message.reply_text(msg, parse_mode="HTML")

    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /remove_user <id>
        Elimina un usuario de la base de datos (revoca rol dinámico).
        """
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            return

        if not context.args or len(context.args) != 1:
            await update.message.reply_text("❌ Uso: /remove_user <id>")
            return

        target_id_str = context.args[0]
        if not target_id_str.isdigit():
            await update.message.reply_text("❌ ID inválido.")
            return
        target_id = int(target_id_str)

        from services.user_service import remove_user

        remove_user(target_id)

        await update.message.reply_text(
            f"✅ Usuario <code>{target_id}</code> removido de la DB.", parse_mode="HTML"
        )

    async def set_staff_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        /set_staff_status <id> <label>
        Cambia el 'custom_status' de un usuario (ej: 'El Chambeador', 'Editor Jefe').
        Solo para Admins.
        """
        uid = update.effective_user.id
        msg = update.effective_message

        if uid not in config.ADMIN_USERS:
            return

        if not context.args or len(context.args) < 2:
            await msg.reply_text(
                "❌ Uso: /set_staff_status <id> <label>\n"
                "Ejemplo: /set_staff_status 123456789 Editor Jefe"
            )
            return

        target_id_str = context.args[0]
        if not target_id_str.isdigit():
            await msg.reply_text("❌ ID inválido.")
            return
        target_id = int(target_id_str)

        new_label = " ".join(context.args[1:])

        # Importar update_user_status_label
        from services.user_service import update_user_status_label

        try:
            update_user_status_label(target_id, new_label)
            await msg.reply_text(
                f"✅ Status actualizado para <code>{target_id}</code>: <b>{new_label}</b>",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Error set_staff_status: {e}")
            await update.effective_message.reply_text(f"❌ Error: {str(e)}")

            os._exit(1)

    async def get_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Devuelve el ID del chat actual y del usuario (admin only)."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            return

        chat_id = update.effective_chat.id
        thread_id = (
            update.message.message_thread_id
            if update.message.message_thread_id
            else "N/A"
        )

        msg = (
            f"🆔 <b>Info del Chat</b>\n"
            f"Chat ID: <code>{chat_id}</code>\n"
            f"User ID: <code>{uid}</code>\n"
            f"Thread ID: <code>{thread_id}</code>"
        )

        try:
            await context.bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
            # Si se pidió desde un grupo, avisar discretamente o reaccionar
            if update.effective_chat.type != "private":
                await update.message.reply_text(
                    "✅ Info enviada al privado.", quote=True
                )
        except Exception as e:
            # Fallback si no se puede enviar al privado (e.g. usuario no inició bot)
            await update.message.reply_text(
                f"❌ No pude enviarte MP (¿me has iniciado?). Aquí tienes:\n\n{msg}",
                parse_mode="HTML",
            )

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Existing reset command implementation
        """Resetea el contador de descargas de un usuario (solo admins)."""
        uid = update.effective_user.id

        # Verificar que sea admin
        if uid not in config.ADMIN_USERS:
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando."
            )
            return

        # Verificar argumentos
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Uso incorrecto.\n"
                "Uso: /reset <user_id>\n"
                "Ejemplo: /reset 123456789"
            )
            return

        try:
            target_uid = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ El ID debe ser un número válido.")
            return

        # Resetear descargas
        from utils.download_limiter import save_download

        # Paranoid import to ensure singleton consistency
        from core.state_manager import state_manager

        user_state = state_manager.get_user_state(target_uid)
        old_count = user_state.get("downloads_used", 0)
        user_state["downloads_used"] = 0

        # Actualizar persistencia
        save_download(target_uid, 0)

        # Verify in log
        logger.info(f"Reset confirmed. Mem: {user_state.get('downloads_used')}")

        await update.message.reply_text(
            f"✅ Contador de descargas reseteado para el usuario {target_uid}.\n"
            f"Descargas usadas anteriormente: {old_count}"
        )

        logger.info(
            f"Admin {uid} reseteó descargas de usuario {target_uid} (antes: {old_count})"
        )
