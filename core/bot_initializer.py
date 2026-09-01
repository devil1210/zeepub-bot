import asyncio
import json
import logging
import os

from config.config_settings import config
from services.backup_scheduler import start_backup_scheduler
from services.daily_reset_scheduler import start_daily_reset_scheduler
from services.facebook_sync_service import start_facebook_sync_scheduler
from services.publisher.publisher_scheduler import start_publisher_scheduler
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
            ("publisher", start_publisher_scheduler),
            ("facebook_sync", lambda _: start_facebook_sync_scheduler()),
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
                # Recommendations and Publisher now expect application for job_queue
                if name in ["recommendations", "publisher"]:
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
                from services.version_service import VersionService

                v_info = await VersionService.get_version_status()
                v = v_info.get("local_hash", get_version_string())
                branch = v_info.get("branch", "")
                changelog = v_info.get("changelog", [])

                cl_text = ""
                if changelog:
                    cl_text = "\n\n<b>📝 Mejoras aplicadas:</b>\n" + "\n".join(f"• {c}" for c in changelog[:5])

                logger.info(f"Sending update success message to {chat_id} (Thread: {thread_id})")
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"✅ <b>¡Actualización Exitosa!</b>\n"
                            f"🤖 <b>ZeePub Bot</b> está en línea y actualizado en la rama <code>{escapar_html(branch)}</code> (<code>{escapar_html(v)}</code>). 🚀"
                            f"{cl_text}"
                        ),
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
                except Exception as e:
                    logger.warning(f"Error enviando notificación HTML de update, reintentando texto plano: {e}")
                    await bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"✅ ¡Actualización Exitosa!\n"
                            f"🤖 ZeePub Bot está en línea en la rama {branch} ({v}). 🚀\n"
                        ),
                        message_thread_id=thread_id,
                    )
            else:
                logger.warning("Update state file found but no chat_id key")

            os.remove(state_path)

        except Exception as e:
            logger.error(f"Error notificando update: {e}", exc_info=True)

    @staticmethod
    async def register_bot_commands(bot):
        """Registra los comandos interactivos en Telegram BotFather / Menú de comandos."""
        from telegram import (
            BotCommand,
            BotCommandScopeAllChatAdministrators,
            BotCommandScopeAllGroupChats,
            BotCommandScopeAllPrivateChats,
            BotCommandScopeChat,
            BotCommandScopeDefault,
        )

        public_commands = [
            BotCommand("start", "🏠 Iniciar bot y menú principal"),
            BotCommand("buscar", "🔍 Buscar novelas por título o autor"),
            BotCommand("catalogo", "📚 Explorar catálogo completo"),
            BotCommand("series", "📖 Explorar catálogo por series"),
            BotCommand("status", "👤 Ver perfil y descargas restantes"),
            BotCommand("donar", "⭐ Información de membresías VIP"),
            BotCommand("ayuda", "ℹ️ Guía de uso y comandos"),
            BotCommand("cancel", "❌ Cancelar acción activa"),
        ]

        admin_commands = list(public_commands) + [
            BotCommand("admin", "🛠️ Panel de control y mantenimiento"),
            BotCommand("scan_library", "🔄 Escanear e indexar biblioteca"),
            BotCommand("update_system", "🚀 Comprobar / actualizar versión"),
            BotCommand("stats", "📊 Estadísticas globales del sistema"),
            BotCommand("id", "🆔 Ver ID de usuario, chat y tema actual"),
            BotCommand("upload_epub", "📤 Subir libro a la biblioteca"),
            BotCommand("broadcast", "📢 Enviar mensaje global a usuarios"),
        ]

        try:
            await bot.set_my_commands(public_commands, scope=BotCommandScopeDefault())
            await bot.set_my_commands(public_commands, scope=BotCommandScopeAllPrivateChats())
            await bot.set_my_commands(public_commands, scope=BotCommandScopeAllGroupChats())
            await bot.set_my_commands(public_commands, scope=BotCommandScopeAllChatAdministrators())

            for admin_id in getattr(config, "ADMIN_USERS", []):
                try:
                    await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
                    await asyncio.sleep(0.2)
                except Exception:
                    pass

            logger.info("Comandos del bot registrados exitosamente en Telegram.")
        except Exception as e:
            logger.warning(f"No se pudieron registrar los comandos en Telegram: {e}")
