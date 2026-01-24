import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from plugins.base_plugin import BasePlugin
from services.settings_service import SettingsService, get_setting
from services.user_service import (
    remove_user,
    update_user_nickname,
    update_user_status_label,
    upsert_user,
)
from utils.download_limiter import save_download
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class UserManagerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "user_manager"

    @property
    def version(self) -> str:
        return "1.2.0"

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
            app.add_handler(CommandHandler("set_rol", self.set_rol))
            app.add_handler(CommandHandler("set_apodo", self.set_apodo))
            app.add_handler(CommandHandler("reset", self.reset_command))
            app.add_handler(CommandHandler("id", self.get_id))
            app.add_handler(CommandHandler("approve_donation", self.approve_donation))
            app.add_handler(CommandHandler("reject_donation", self.reject_donation))
            app.add_handler(CommandHandler("refresh_user", self.refresh_user_command))

            logger.info("Plugin UserManager: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin UserManager: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    def _is_admin(self, uid: int) -> bool:
        return uid in config.ADMIN_USERS

    def _get_target_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Helper para obtener (user_id, user_first_name) ya sea de argumentos
        o del mensaje respondido (reply).
        Retorna (target_id, target_name_or_none) o (None, None) si falla.
        """
        # 1. Check Reply
        if update.message.reply_to_message:
            r_user = update.message.reply_to_message.from_user
            return r_user.id, r_user.first_name

        # 2. Check Arguments (first arg is ID)
        if context.args and len(context.args) > 0 and context.args[0].isdigit():
            return int(context.args[0]), "Usuario"

        return None, None

    async def add_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /add_user <id> <rol> [meses]
        Agrega un usuario con un rol específico y duración opcional.
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        target_id, target_name = self._get_target_user(update, context)

        # Validation Logic adjusted for "reply" usage
        # If replied, args[0] might be role. If not replied, args[0] is ID, args[1] is role.

        role = None
        duration_arg_idx = -1

        if update.message.reply_to_message:
            # Usage: Reply + /add_user <rol> [meses]
            if not target_id:
                # Should not happen if _get_target_user check passed, but safety first
                return

            if not context.args or len(context.args) < 1:
                await update.message.reply_text(
                    "❌ Al responder, indica al menos el rol.\nEj: /add_user vip",
                    message_thread_id=thread_id,
                )
                return
            role = context.args[0].lower()
            if len(context.args) > 1:
                duration_arg_idx = 1
        else:
            # Usage: /add_user <id> <rol> [meses]
            if not target_id:
                await update.message.reply_text(
                    "❌ Uso: /add_user <id> <rol> [meses] (o responde a un mensaje).",
                    message_thread_id=thread_id,
                )
                return

            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Faltan argumentos. Uso: /add_user <id> <rol> [meses]",
                    message_thread_id=thread_id,
                )
                return

            role = context.args[1].lower()
            if len(context.args) > 2:
                duration_arg_idx = 2

        valid_levels = [
            "white",
            "vip",
            "premium",
            "staff",
            "admin",
            "banned",
            "free",
            "user",
        ]
        if role not in valid_levels:
            await update.message.reply_text(
                f"❌ Nivel inválido. Use: {', '.join(valid_levels)}",
                message_thread_id=thread_id,
            )
            return

        # Determine duration
        duration = None
        duration_days = None

        if duration_arg_idx != -1 and len(context.args) > duration_arg_idx:
            val_str = context.args[duration_arg_idx]
            if val_str.isdigit():
                val = int(val_str)
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
            level=role,
            duration_months=duration,
            created_by=uid,
            duration_days=duration_days,
        )

        msg = f"✅ Usuario <code>{target_id}</code> ({target_name}) agregado como <b>{role.capitalize()}</b>"
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

    async def set_rol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /set_rol <id> <label>
        Cambia el 'role' (label) de un usuario (ej: 'El Chambeador', 'Editor Jefe').
        Solo para Admins.
        """
        uid = update.effective_user.id
        msg = update.effective_message
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        target_id, target_name = self._get_target_user(update, context)

        if not target_id:
            await msg.reply_text(
                "❌ Uso: /set_rol <id> <label> (o responde a un mensaje).",
                message_thread_id=thread_id,
            )
            return

        # Parse label
        # If reply, everything in args is label
        # If ID arg, args[0] is ID, usage args[1:] is label

        args_start_idx = 0
        if not update.message.reply_to_message:
            # First arg was consumed as ID
            args_start_idx = 1
            if len(context.args) < 2:
                await msg.reply_text(
                    "❌ Indica el rol/label.", message_thread_id=thread_id
                )
                return
        else:
            if len(context.args) < 1:
                await msg.reply_text(
                    "❌ Al responder, indica el rol/label.",
                    message_thread_id=thread_id,
                )
                return

        # Check for deletion keywords
        delete_keywords = ["borrar", "eliminar", "none", "null", "remove", "off"]

        first_word = context.args[args_start_idx].lower()

        # If only one word and it is a delete keyword
        if len(context.args) == args_start_idx + 1 and first_word in delete_keywords:
            new_label = None
            success_msg = (
                f"✅ Rol/label eliminado para <code>{target_id}</code> (vuelve a default)."
            )
        else:
            new_label = " ".join(context.args[args_start_idx:])
            success_msg = f"✅ Rol/label actualizado para <code>{target_id}</code> ({target_name}): <b>{new_label}</b>"

        try:
            await update_user_status_label(target_id, new_label)
            await msg.reply_text(
                success_msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
        except Exception as e:
            logger.error(f"Error set_rol: {e}")
            await msg.reply_text(f"❌ Error: {str(e)}", message_thread_id=thread_id)

    async def set_apodo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /set_apodo <id> <apodo>
        Establece el nickname/apodo de un usuario.
        """
        uid = update.effective_user.id
        msg = update.effective_message
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        target_id, target_name = self._get_target_user(update, context)

        if not target_id:
            await msg.reply_text(
                "❌ Uso: /set_apodo <id> <apodo> (o responde a un mensaje).",
                message_thread_id=thread_id,
            )
            return

        # Parse Apodo
        args_start_idx = 0
        if not update.message.reply_to_message:
            args_start_idx = 1
            if len(context.args) < 2:
                await msg.reply_text("❌ Indica el apodo", message_thread_id=thread_id)
                return
        else:
            if len(context.args) < 1:
                await msg.reply_text(
                    "❌ Al responder, indica el apodo.", message_thread_id=thread_id
                )
                return

        # Check for deletion keywords
        delete_keywords = ["borrar", "eliminar", "none", "null", "remove", "off"]
        first_word = context.args[args_start_idx].lower()

        if len(context.args) == args_start_idx + 1 and first_word in delete_keywords:
            new_label = None
            success_msg = f"✅ Apodo eliminado para <code>{target_id}</code>."
        else:
            new_label = " ".join(context.args[args_start_idx:])
            success_msg = f"✅ Apodo actualizado para <code>{target_id}</code> ({target_name}): <b>{new_label}</b>"

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
        except Exception:
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

    async def approve_donation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        /approve_donation <id> <rol> [meses]
        Aprueba una donación, actualiza el nivel del usuario y le notifica.
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        target_id, target_name = self._get_target_user(update, context)

        # Parse role and duration similar to add_user
        role = None
        duration_arg_idx = -1

        if update.message.reply_to_message:
            if not context.args or len(context.args) < 1:
                await update.message.reply_text(
                    "❌ Al responder, indica al menos el rol.\nEj: /approve_donation vip 30",
                    message_thread_id=thread_id,
                )
                return
            role = context.args[0].lower()
            if len(context.args) > 1:
                duration_arg_idx = 1
        else:
            if not target_id:
                await update.message.reply_text(
                    "❌ Uso: /approve_donation <id> <rol> [meses] (o responde a un mensaje).",
                    message_thread_id=thread_id,
                )
                return

            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Faltan argumentos. Uso: /approve_donation <id> <rol> [meses]",
                    message_thread_id=thread_id,
                )
                return

            role = context.args[1].lower()
            if len(context.args) > 2:
                duration_arg_idx = 2

        valid_levels = ["white", "vip", "premium", "staff", "admin"]
        if role not in valid_levels:
            await update.message.reply_text(
                f"❌ Nivel inválido. Use: {', '.join(valid_levels)}",
                message_thread_id=thread_id,
            )
            return

        # Parse duration
        duration_days = None
        if duration_arg_idx != -1 and len(context.args) > duration_arg_idx:
            val_str = context.args[duration_arg_idx]
            if val_str.isdigit():
                duration_days = int(val_str) * 30  # meses -> días

        # Update user
        result = await upsert_user(target_id, level=role, duration_days=duration_days)

        # Send notification to user
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        nivel_text = role.capitalize()
        duracion_text = str(duration_days) if duration_days else None

        base_text = f"✅ Donación Verificada!\n\nNuevo nivel: {nivel_text}"
        if duration_days:
            base_text += f"\nDuración: {duration_days} días"
        text = base_text

        if cms and cms.enabled:
            text = await cms.get_text(
                "donation_approved", Nivel=nivel_text, Duración=duracion_text
            )

        try:
            await context.bot.send_message(
                chat_id=target_id, text=text, parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al usuario {target_id}: {e}")

        # Clear waiting state
        st = state_manager.get_user_state(target_id)
        st.pop("waiting_for_donation_proof", None)

        # Confirm to admin
        await update.message.reply_text(
            f"✅ Donación aprobada para {target_id}.\nNivel: {role}\nNotificación enviada.",
            message_thread_id=thread_id,
        )

    async def reject_donation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /reject_donation <id>
        Rechaza una donación y notifica al usuario.
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        target_id, target_name = self._get_target_user(update, context)
        if not target_id:
            await update.message.reply_text(
                "❌ Uso: /reject_donation <id> (o responde a un mensaje)",
                message_thread_id=thread_id,
            )
            return

        # Send rejection notification
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_text = "⚠️ Comprobante No Válido\n\nLamentablemente, tu comprobante de donación no pudo ser verificado."
        text = base_text

        if cms and cms.enabled:
            text = await cms.get_text("donation_rejected")

        try:
            await context.bot.send_message(
                chat_id=target_id, text=text, parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al usuario {target_id}: {e}")

        # Clear waiting state
        st = state_manager.get_user_state(target_id)
        st.pop("waiting_for_donation_proof", None)

        await update.message.reply_text(
            f"❌ Donación rechazada para {target_id}.\nNotificación enviada.",
            message_thread_id=thread_id,
        )

    async def refresh_user_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        /refresh_user <id>
        Limpia el caché del bot para un usuario específico.
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        target_id, target_name = self._get_target_user(update, context)
        if not target_id:
            await update.message.reply_text(
                "❌ Uso: /refresh_user <id> (o responde a un mensaje).",
                message_thread_id=thread_id,
            )
            return

        from services.user_service import invalidate_user_cache

        await invalidate_user_cache(target_id)

        # Limpiar también el contador de descargas del state_manager para forzar re-lectura si fuera necesario
        # Aunque state_manager no suele cachear roles permanently, invalidar el usuario asegura que el bot recargue todo.

        await update.message.reply_text(
            f"✅ Caché limpiado para el usuario <code>{target_id}</code>. Los cambios de nivel deberían verse al reabrir la Mini App.",
            parse_mode="HTML",
            message_thread_id=thread_id,
        )
