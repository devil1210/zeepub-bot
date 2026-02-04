import json
import logging
import os

from config.config_settings import config
from services.backup_scheduler import start_backup_scheduler
from services.daily_reset_scheduler import start_daily_reset_scheduler
from services.recommendation_scheduler import start_recommendations_scheduler
from services.weekly_reports import start_weekly_scheduler
from utils.download_limiter import load_downloads
from utils.helpers import escapar_html, get_last_commit_message, get_version_string
from utils.metrics import metrics

logger = logging.getLogger(__name__)


class BotInitializer:
    """Maneja la inicialización de schedulers y notificaciones."""

    @staticmethod
    async def initialize_schedulers(application):
        """Inicializa todos los schedulers del sistema y métricas."""
        # Iniciar servidor de métricas
        if config.ENABLE_METRICS:
            metrics.start_server(config.METRICS_PORT)

        # Bot instance for legacy compatibility if needed by funcs
        bot = application.bot

        schedulers = [
            ("weekly_reports", start_weekly_scheduler),
            ("backup", start_backup_scheduler),
            ("daily_reset", start_daily_reset_scheduler),
            ("recommendations", start_recommendations_scheduler),
        ]

        # Pre-load needed data for schedulers if any
        try:
            load_downloads()
        except Exception as e:
            logger.error(f"Error loading downloads persistence: {e}")

        for name, scheduler_func in schedulers:
            try:
                # Some funcs expect bot, some expect application.
                # Weekly, Backup, Daily expect bot (legacy behavior)
                # Recommendations now expects application for job_queue
                if name == "recommendations":
                    scheduler_func(application)
                else:
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
            with open(state_path) as f:
                state = json.load(f)

            chat_id = state.get("chat_id")
            thread_id = state.get("message_thread_id")

            if chat_id:
                v = get_version_string()
                commit_msg = get_last_commit_message()
                logger.info(f"Sending update success message to {chat_id} (Thread: {thread_id})")
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"✅ <b>¡Actualización Completada!</b>\n"
                            f"🤖 ZeePub Bot {escapar_html(v)} está en línea. 🚀\n\n"
                            f"📝 <b>Cambios:</b> {escapar_html(commit_msg)}"
                        ),
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
                except Exception as e:
                    logger.warning(
                        f"Error enviando notificación HTML de update, reintentando texto plano: {e}"
                    )
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"✅ ¡Actualización Completada!\n"
                            f"🤖 ZeePub Bot {v} está en línea. 🚀\n\n"
                            f"📝 Cambios: {commit_msg}"
                        ),
                        message_thread_id=thread_id,
                    )
            else:
                logger.warning("Update state file found but no chat_id key")

            os.remove(state_path)

        except Exception as e:
            logger.error(f"Error notificando update: {e}", exc_info=True)
