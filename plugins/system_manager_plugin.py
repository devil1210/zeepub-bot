import asyncio
import logging
import os
import subprocess

import httpx
from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from services.settings_service import SettingsService
from utils.helpers import get_thread_id

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
            app.add_handler(CommandHandler("set_version", self.set_version))

            # Callback Handlers
            app.add_handler(
                CallbackQueryHandler(self.set_log_level_callback, pattern=r"^setlog\|")
            )

            # Auto-update check job (Every 6 hours = 21600 seconds)
            if app.job_queue:
                app.job_queue.run_repeating(
                    self.check_for_updates_job, interval=21600, first=60
                )
                logger.info("SystemManager: Auto-update check scheduled (every 6h).")

            logger.info("Plugin SystemManager: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin SystemManager: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def check_for_updates_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Tarea programada para revisar actualizaciones."""
        try:
            local_hash, remote_hash = await self._get_git_hashes()

            if local_hash == "Desconocido" or remote_hash == "Desconocido":
                return

            if local_hash != remote_hash:
                # Check if we already notified recently?
                # For now simplify: Just notify. The interval is 6 hours, so it's not too spammy.
                # Maybe checking a stored state would be better, but let's start simple.

                msg = (
                    f"🔔 <b>Actualización Disponible</b>\n\n"
                    f"Actual: <code>{local_hash}</code>\n"
                    f"Nueva: <code>{remote_hash}</code>\n\n"
                    f"Usa /update_system para aplicar cambios."
                )

                for admin_id in config.ADMIN_USERS:
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id, text=msg, parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Could not notify admin {admin_id} about update: {e}"
                        )
        except Exception as e:
            logger.error(f"Error in check_for_updates_job: {e}")

    async def _get_git_hashes(self):
        """Helper to get local and remote hashes."""
        # 1. Local
        try:
            if os.path.exists("version_hash.txt"):
                with open("version_hash.txt") as f:
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

        # 2. Remote
        remote_hash = "Desconocido"
        try:
            branch = config.GIT_BRANCH or "main"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.github.com/repos/devil1210/zeepub-bot/commits/{branch}",
                    headers={"User-Agent": "ZeePubBot/2.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    remote_hash = data.get("sha", "")[:7]
        except Exception as e:
            logger.error(f"Error checking remote git via API: {e}")

        return local_hash, remote_hash

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

            # Update message to show confirmation (legacy behavior: no buttons)
            # Retry logic for network stability
            try:
                await query.edit_message_text(
                    f"✅ Nivel de log cambiado a <b>{level_str}</b>", parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Error editing message (attempt 1): {e}. Retrying...")
                await asyncio.sleep(0.5)
                try:
                    await query.edit_message_text(
                        f"✅ Nivel de log cambiado a <b>{level_str}</b>",
                        parse_mode="HTML",
                    )
                except Exception as e2:
                    logger.warning(
                        f"Error editing message (attempt 2): {e2}. Fallback to delete+send."
                    )
                    try:
                        await query.message.delete()
                    except Exception:
                        pass

                    try:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=f"✅ Nivel de log cambiado a <b>{level_str}</b>",
                            parse_mode="HTML",
                        )
                    except Exception as e3:
                        logger.error(f"Failed to send confirmation message: {e3}")
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
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        status_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⏳ Comprobando versiones...",
            message_thread_id=thread_id,
        )

        # 1. & 2. Obtener hashes
        try:
            local_hash, remote_hash = await self._get_git_hashes()
        except Exception:
            local_hash = "Desconocido"
            remote_hash = "Desconocido"

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

                # Watchtower will detect the new image and restart the container automatically
                # Waiting a bit to let Watchtower do its job
                import asyncio

                await asyncio.sleep(10)

        else:
            await status_msg.edit_text(
                f"✅ <b>Sistema actualizado.</b>\nVersión: <code>{local_hash}</code>",
                parse_mode="HTML",
            )

    async def set_version(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /set_version <tag>
        Cambia la versión del bot en docker-compose.yml.
        """
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not self._is_admin(uid):
            return

        if not context.args:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Uso: /set_version <tag>\nEjemplo: /set_version 4.5.1",
                message_thread_id=thread_id,
            )
            return

        new_tag = context.args[0].strip()
        compose_path = "docker-compose.yml"

        if not os.path.exists(compose_path):
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ No se encontró docker-compose.yml en el directorio raíz.",
                message_thread_id=thread_id,
            )
            return

        try:
            import re

            with open(compose_path) as f:
                content = f.read()

            # Pattern to match the image tag for zeepubs_bot service
            # Supports both commented out and active image lines for robustness,
            # but targets the ghcr.io one by default as seen in the file.
            pattern = r"(image:\s+ghcr\.io/devil1210/zeepub-bot:)(.*)"

            if not re.search(pattern, content):
                # Fallback for standard docker hub image if ghcr is not used or commented
                pattern = r"(image:\s+devil1210/zeepub-bot:)(.*)"

            if not re.search(pattern, content):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ No se encontró la línea 'image' esperada en docker-compose.yml",
                    message_thread_id=thread_id,
                )
                return

            new_content = re.sub(pattern, rf"\g<1>{new_tag}", content)

            with open(compose_path, "w") as f:
                f.write(new_content)

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"✅ <b>docker-compose.yml actualizado</b>\n\n"
                    f"Nueva versión configurada: <code>{new_tag}</code>\n\n"
                    f"⚠️ Usa /update_system para aplicar los cambios ahora."
                ),
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            logger.info(
                f"Admin {uid} cambió la versión en docker-compose.yml a: {new_tag}"
            )
        except Exception as e:
            logger.error(f"Error en set_version: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ Error al actualizar el archivo: {e}",
                message_thread_id=thread_id,
            )
