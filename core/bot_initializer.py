import logging
from services.weekly_reports import start_weekly_scheduler
from services.backup_scheduler import start_backup_scheduler
from services.daily_reset_scheduler import start_daily_reset_scheduler
from utils.download_limiter import load_downloads
from utils.helpers import get_version_string, get_last_commit_message
import os
import json

logger = logging.getLogger(__name__)

from utils.metrics import metrics


class BotInitializer:
    """Maneja la inicialización de schedulers y notificaciones."""

    @staticmethod
    async def initialize_schedulers(bot):
        """Inicializa todos los schedulers del sistema y métricas."""
        # Iniciar servidor de métricas
        metrics.start_server(8000)

        schedulers = [
            ("weekly_reports", start_weekly_scheduler),
            ("backup", start_backup_scheduler),
            ("daily_reset", start_daily_reset_scheduler),
        ]

        # Pre-load needed data for schedulers if any
        try:
            load_downloads()
        except Exception as e:
            logger.error(f"Error loading downloads persistence: {e}")

        for name, scheduler_func in schedulers:
            try:
                scheduler_func(bot)
                logger.info(f"{name} scheduler iniciado")
            except Exception as e:
                logger.error(f"Error iniciando {name}: {e}", exc_info=True)

    @staticmethod
    async def check_update_state(bot):
        """Verifica y notifica actualizaciones completadas (Watchtower)."""
        state_path = "data/update_state.json"

        if not os.path.exists(state_path):
            logger.info(f"No update state file found at {state_path}")
            return

        logger.info(f"Found update state file at {state_path}")
        try:
            with open(state_path, "r") as f:
                state = json.load(f)

            chat_id = state.get("chat_id")
            thread_id = state.get("message_thread_id")

            if chat_id:
                v = get_version_string()
                commit_msg = get_last_commit_message()
                logger.info(
                    f"Sending update success message to {chat_id} (Thread: {thread_id})"
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"✅ <b>¡Actualización Completada!</b>\n"
                        f"🤖 ZeePub Bot v{v} está en línea. 🚀\n\n"
                        f"📝 <i>Cambios:</i> {commit_msg}"
                    ),
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                logger.warning("Update state file found but no chat_id key")

            os.remove(state_path)

        except Exception as e:
            logger.error(f"Error notificando update: {e}", exc_info=True)
