import logging
import subprocess
import os
import httpx
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id
from services.settings_service import SettingsService

logger = logging.getLogger(__name__)


class SystemManagerPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "system_manager"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Gestión del sistema, actualizaciones y configuración técnica."

    def __init__(self):
        self.settings_service = SettingsService()
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = config.ENABLE_SYSTEM_MANAGER

        if not self.enabled:
            logger.info("Plugin SystemManager desactivado por configuración.")
            return False

        try:
            app = bot_instance
            # Admin commands
            app.add_handler(CommandHandler("update_system", self.update_system))
            app.add_handler(
                CommandHandler("set_auto_delete_time", self.set_auto_delete_time)
            )
            app.add_handler(CommandHandler("setlog", self.setlog))

            # Callback Handlers
            app.add_handler(
                CallbackQueryHandler(self.set_log_level_callback, pattern=r"^setlog\|")
            )

            logger.info("Plugin SystemManager: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin SystemManager: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    def _is_admin(self, uid: int) -> bool:
        return uid in config.ADMIN_USERS

    async def setlog(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra botones para cambiar el nivel de log."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        current_level_int = logging.getLogger().getEffectiveLevel()
        current_level_name = logging.getLevelName(current_level_int)

        keyboard = [
            [
                InlineKeyboardButton("DEBUG", callback_data="setlog|DEBUG"),
                InlineKeyboardButton("INFO", callback_data="setlog|INFO"),
            ],
            [
                InlineKeyboardButton("WARNING", callback_data="setlog|WARNING"),
                InlineKeyboardButton("ERROR", callback_data="setlog|ERROR"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔧 <b>Configuración de Logs</b>\n\nNivel actual: <b>{current_level_name}</b>\nSelecciona un nuevo nivel:",
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

    async def set_log_level_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Callback para botones de /setlog."""
        query = update.callback_query
        uid = update.effective_user.id

        if not self._is_admin(uid):
            await query.answer("⛔ No tienes permisos.", show_alert=True)
            return

        try:
            data = query.data
            _, level_str = data.split("|", 1)
            level_str = level_str.upper()

            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if level_str not in valid_levels:
                await query.answer(f"Nivel inválido: {level_str}", show_alert=True)
                return

            new_level = getattr(logging, level_str)

            # 1. Root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(new_level)
            
            # 2. Update ALL handlers on root logger
            for handler in root_logger.handlers:
                handler.setLevel(new_level)

            # 3. Specific loggers
            loggers_to_update = [
                "uvicorn",
                "uvicorn.access",
                "httpx",
                "httpcore",
                "httpcore.http11",
                "httpcore.connection",
                "telegram",
                "telegram.ext",
                "apscheduler",
            ]
            for logger_name in loggers_to_update:
                logger_instance = logging.getLogger(logger_name)
                logger_instance.setLevel(new_level)
                # Also update handlers on each specific logger
                for handler in logger_instance.handlers:
                    handler.setLevel(new_level)

            logger.log(
                new_level,
                f"Log level cambiado a {level_str} por admin {uid} (vía botón)",
            )

            # Rebuild keyboard to keep UI interactive
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = [
                [
                    InlineKeyboardButton("DEBUG", callback_data="setlog|DEBUG"),
                    InlineKeyboardButton("INFO", callback_data="setlog|INFO"),
                ],
                [
                    InlineKeyboardButton("WARNING", callback_data="setlog|WARNING"),
                    InlineKeyboardButton("ERROR", callback_data="setlog|ERROR"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                f"🔧 <b>Configuración de Logs</b>\n\nNivel actual: <b>{level_str}</b>\nSelecciona un nuevo nivel:",
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            await query.answer(f"Nivel cambiado a {level_str}")

        except Exception as e:
            logger.error(f"Error en set_log_level_callback: {e}", exc_info=True)
            await query.answer("Error al cambiar nivel")

    async def set_auto_delete_time(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        /set_auto_delete_time <minutos>
        Configura el tiempo de auto-borrado para descargas de admins en grupos.
        """
        uid = update.effective_user.id
        msg = update.effective_message
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        if not context.args or not context.args[0].isdigit():
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Uso: /set_auto_delete_time <minutos>",
                message_thread_id=thread_id,
            )
            return

        minutes = int(context.args[0])

        try:
            await self.settings_service.set_setting("auto_delete_time", minutes)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"✅ Tiempo de auto-borrado configurado a: <b>{minutes} minutos</b>",
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
        except Exception as e:
            logger.error(f"Error set_auto_delete_time: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Error al guardar configuración.",
                message_thread_id=thread_id,
            )

    async def update_system(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /update_system
        Verifica si hay cambios en git antes de invocar a Watchtower.
        """
        uid = update.effective_user.id
        msg = update.effective_message
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        status_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏳ Comprobando versiones...",
            message_thread_id=thread_id,
        )

        # 1. Obtener Hash Local
        try:
            if os.path.exists("version_hash.txt"):
                with open("version_hash.txt", "r") as f:
                    local_hash = f.read().strip()[:7]
            else:
                local_hash = (
                    subprocess.check_output(
                        ["git", "rev-parse", "--short", "HEAD"],
                        stderr=subprocess.STDOUT,
                    )
                    .decode()
                    .strip()
                )
        except Exception:
            local_hash = "Desconocido"

        # 2. Obtener Hash Remoto
        remote_hash = "Desconocido"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.github.com/repos/devil1210/zeepub-bot/commits/main",
                    headers={"User-Agent": "ZeePubBot/2.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remote_hash = data.get("sha", "")[:7]
        except Exception as e:
            logger.error(f"Error checking remote git via API: {e}")

        # 3. Comparar versiones
        force_update = False
        if context.args and "force" in context.args[0].lower():
            force_update = True
            logger.info(f"Update forzado por usuario {uid}")

        if local_hash != remote_hash or force_update:
            msg_text = (
                f"🔹 <b>Versión Local:</b> <code>{local_hash}</code>\n"
                f"🔸 <b>Versión Remota:</b> <code>{remote_hash}</code>\n\n"
            )

            if force_update:
                msg_text += "⚠️ <b>Actualización Forzada.</b> Reinstalando sistema...\n"
            else:
                msg_text += (
                    "🚀 <b>Nueva versión detectada.</b> Iniciando actualización...\n"
                )

            await status_msg.edit_text(msg_text, parse_mode="HTML")

            # 4. Trigger Update (Invocar Watchtower)
            # Guardar estado antes de trigger
            try:
                import json

                os.makedirs("data", exist_ok=True)
                # Save CURRENT CHAT ID (not user ID) to notify in the same thread/group (if topic)
                state = {
                    "chat_id": update.effective_chat.id,
                    "message_id": status_msg.message_id,
                    "message_thread_id": thread_id,
                }
                with open("data/update_state.json", "w") as f:
                    json.dump(state, f)
                logger.info(f"Saved update state to data/update_state.json: {state}")
            except Exception as e:
                logger.error(f"No se pudo guardar update_state: {e}")

            from services.maintenance_service import trigger_watchtower_update

            success, message = await trigger_watchtower_update()

            if not success:
                try:
                    if os.path.exists("data/update_state.json"):
                        os.remove("data/update_state.json")
                except Exception:
                    pass

                await status_msg.edit_text(message, parse_mode="HTML")
            else:
                message += "\n\n⏳ <b>El sistema se reiniciará en breve...</b>"
                await status_msg.edit_text(message, parse_mode="HTML")

                # Fallback suicida
                import asyncio
                import sys

                await asyncio.sleep(10)
                logger.warning(
                    "Watchtower didn't kill us in time. Committing sudoku..."
                )
                sys.exit(0)

        else:
            await status_msg.edit_text(
                f"✅ <b>Sistema actualizado.</b>\n"
                f"Versión: <code>{local_hash}</code>",
                parse_mode="HTML",
            )
