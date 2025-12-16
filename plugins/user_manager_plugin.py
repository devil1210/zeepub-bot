import logging
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id
from services.user_service import upsert_user, remove_user, update_user_status_label, update_user_nickname
from services.settings_service import SettingsService, get_setting
from utils.download_limiter import save_download
from core.state_manager import state_manager

logger = logging.getLogger(__name__)


class UserManagerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "user_manager"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Gestión de usuarios: altas, bajas, staff y utilidades de ID."

    def __init__(self):
        self.settings_service = SettingsService()
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = config.ENABLE_USER_MANAGER

        if not self.enabled:
            logger.info("Plugin UserManager desactivado por configuración.")
            return False

        try:
            app = bot_instance
            # Admin commands
            app.add_handler(CommandHandler("add_user", self.add_user))
            app.add_handler(CommandHandler("remove_user", self.remove_user))
            app.add_handler(CommandHandler("set_staff_status", self.set_staff_status))
            app.add_handler(CommandHandler("set_apodo", self.set_apodo))
            app.add_handler(CommandHandler("reset", self.reset_command))
            app.add_handler(CommandHandler("id", self.get_id))

            logger.info("Plugin UserManager: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin UserManager: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    def _is_admin(self, uid: int) -> bool:
        return uid in config.ADMIN_USERS

    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /add_user <id> <rol> [meses]
        Agrega un usuario con un rol específico y duración opcional.
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: /add_user <id> <rol> [meses]\n"
                "Roles: white, vip, premium, staff\n"
                "Ejemplo: /add_user 123456789 vip 6",
                message_thread_id=thread_id,
            )
            return

        target_id_str = context.args[0]
        role = context.args[1].lower()

        if not target_id_str.isdigit():
            await update.message.reply_text(
                "❌ ID inválido.", message_thread_id=thread_id
            )
            return
        target_id = int(target_id_str)

        valid_roles = ["white", "vip", "premium", "staff", "banned", "free", "user"]
        if role not in valid_roles:
            await update.message.reply_text(
                f"❌ Rol inválido. Use: {', '.join(valid_roles)}",
                message_thread_id=thread_id,
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
            if role != "staff" and role != "banned":
                duration = int(get_setting("benefit_duration_months", "6"))

        await upsert_user(
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

        await update.message.reply_text(
            msg, parse_mode="HTML", message_thread_id=thread_id
        )

    async def remove_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /remove_user <id>
        Elimina un usuario de la base de datos (revoca rol dinámico).
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Uso: /remove_user <id>", message_thread_id=thread_id
            )
            return

        target_id_str = context.args[0]
        if not target_id_str.isdigit():
            await update.message.reply_text(
                "❌ ID inválido.", message_thread_id=thread_id
            )
            return
        target_id = int(target_id_str)

        await remove_user(target_id)

        await update.message.reply_text(
            f"✅ Usuario <code>{target_id}</code> removido de la DB.",
            parse_mode="HTML",
            message_thread_id=thread_id,
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
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        if not context.args or len(context.args) < 2:
            await msg.reply_text(
                "❌ Uso: /set_staff_status <id> <label>\n"
                "Ejemplo: /set_staff_status 123456789 Editor Jefe",
                message_thread_id=thread_id,
            )
            return

        target_id_str = context.args[0]
        if not target_id_str.isdigit():
            await msg.reply_text("❌ ID inválido.", message_thread_id=thread_id)
            return
        target_id = int(target_id_str)

        # Check for deletion keywords
        delete_keywords = ["borrar", "eliminar", "none", "null", "remove", "off"]
        if len(context.args) == 2 and context.args[1].lower() in delete_keywords:
            new_label = None
            success_msg = f"✅ Status eliminado para <code>{target_id}</code> (vuelve a default)."
        else:
            new_label = " ".join(context.args[1:])
            success_msg = f"✅ Status actualizado para <code>{target_id}</code>: <b>{new_label}</b>"

        try:
            await update_user_status_label(target_id, new_label)
            await msg.reply_text(
                success_msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
        except Exception as e:
            logger.error(f"Error set_staff_status: {e}")
            await msg.reply_text(f"❌ Error: {str(e)}", message_thread_id=thread_id)

    async def set_apodo(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        /set_apodo <id> <apodo>
        Establece el nickname/apodo de un usuario.
        """
        uid = update.effective_user.id
        msg = update.effective_message
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        if not context.args or len(context.args) < 2:
            await msg.reply_text(
                "❌ Uso: /set_apodo <id> <apodo>\n"
                "Ejemplo: /set_apodo 123456789 El Charly",
                message_thread_id=thread_id,
            )
            return

        target_id_str = context.args[0]
        if not target_id_str.isdigit():
            await msg.reply_text("❌ ID inválido.", message_thread_id=thread_id)
            return
        target_id = int(target_id_str)

        # Check for deletion keywords
        delete_keywords = ["borrar", "eliminar", "none", "null", "remove", "off"]
        if len(context.args) == 2 and context.args[1].lower() in delete_keywords:
            new_label = None
            success_msg = f"✅ Apodo eliminado para <code>{target_id}</code>."
        else:
            new_label = " ".join(context.args[1:])
            success_msg = f"✅ Apodo actualizado para <code>{target_id}</code>: <b>{new_label}</b>"

        try:
            await update_user_nickname(target_id, new_label)
            await msg.reply_text(
                success_msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
        except Exception as e:
            logger.error(f"Error set_apodo: {e}")
            await msg.reply_text(f"❌ Error: {str(e)}", message_thread_id=thread_id)

    async def get_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Devuelve el ID del chat actual y del usuario (admin only)."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        chat_id = update.effective_chat.id
        # thread_id already retrieved via helper

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
                    "✅ Info enviada al privado.",
                    quote=True,
                    message_thread_id=thread_id,
                )
        except Exception as e:
            # Fallback si no se puede enviar al privado (e.g. usuario no inició bot)
            await update.message.reply_text(
                f"❌ No pude enviarte MP (¿me has iniciado?). Aquí tienes:\n\n{msg}",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Resetea el contador de descargas de un usuario (solo admins)."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            await update.message.reply_text(
                "⛔ No tienes permisos para usar este comando.",
                message_thread_id=thread_id,
            )
            return

        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Uso incorrecto.\n"
                "Uso: /reset <user_id>\n"
                "Ejemplo: /reset 123456789",
                message_thread_id=thread_id,
            )
            return

        try:
            target_uid = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ El ID debe ser un número válido.", message_thread_id=thread_id
            )
            return

        user_state = state_manager.get_user_state(target_uid)
        old_count = user_state.get("downloads_used", 0)
        user_state["downloads_used"] = 0

        save_download(target_uid, 0)

        logger.info(
            f"Admin {uid} reseteó descargas de usuario {target_uid} (antes: {old_count})"
        )

        await update.message.reply_text(
            f"✅ Contador de descargas reseteado para el usuario {target_uid}.\n"
            f"Descargas usadas anteriormente: {old_count}",
            message_thread_id=thread_id,
        )
