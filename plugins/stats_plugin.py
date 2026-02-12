import logging
from datetime import datetime

from dateutil import parser as date_parser
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from services.user_service import get_effective_user, get_users_by_level
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class StatsPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "stats_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Estadísticas del bot y de usuarios."

    def __init__(self):
        self.enabled = False

    async def initialize(self, bot_instance) -> bool:
        self.enabled = config.ENABLE_STATS_PLUGIN

        if not self.enabled:
            logger.info("Plugin Stats desactivado por configuración.")
            return False

        try:
            app = bot_instance
            app.add_handler(CommandHandler("stats", self.stats))

            logger.info("Plugin Stats: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Stats: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /stats: muestra estadísticas.
        Uso:
        - /stats: Resumen diario (usuarios activos, descargas, roles).
        - /stats <rol>: Lista usuarios en base de datos con ese rol.
        """
        uid = update.effective_user.id
        # Verificar permisos (Admin o Staff)
        user_info = await get_effective_user(uid)
        level = user_info.get("level", "free")
        is_admin = level == "admin" or uid in config.ADMIN_USERS
        if not is_admin and level != "staff":
            return

        thread_id = get_thread_id(update)

        # Modo Listar Usuarios por Rol: /stats premium
        if context.args:
            target_level = context.args[0].lower()
            users_list = await get_users_by_level(target_level)

            if not users_list:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_no = f"ℹ️ No se encontraron usuarios con el nivel <b>{target_level}</b> en base de datos."
                text_no = (
                    await cms.get_text("stats_no_users", Rol=target_level)
                    if (cms and cms.enabled)
                    else base_no
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text_no,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
                return

            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_header = (
                f"📋 <b>Usuarios con nivel: {target_level.capitalize()}</b> ({len(users_list)})\n\n"
            )
            msg = (
                await cms.get_text(
                    "stats_list_header",
                    Rol=target_level.capitalize(),
                    Cantidad=len(users_list),
                )
                if (cms and cms.enabled)
                else base_header
            )
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
                    # Calcular días restantes
                    now = datetime.utcnow()
                    if isinstance(expires, str):
                        try:
                            expires = date_parser.parse(expires)
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

        # Modo Resumen Diario (Dashboard Completo)
        from services.stats_service import get_stats_summary

        # Obtener métricas paralelas
        stats_day = await get_stats_summary("day")
        stats_month = await get_stats_summary("month")
        stats_year = await get_stats_summary("year")
        stats_all = await get_stats_summary("all")

        cms = context.application.plugin_manager.get_plugin("custom_messages")

        # Definir emojis
        e_dl = "⬇️"
        e_us = "👥"
        e_new = "🆕"

        msg_thread_info = ""
        if thread_id:
            msg_thread_info = f"🆔 <b>Topic ID:</b> <code>{thread_id}</code>\n\n"

        base_summary = (
            "📊 <b>Panel de Estadísticas</b>\n"
            f"{msg_thread_info}"
            "<b>Hoy:</b>\n"
            f"{e_dl} Descargas: {stats_day['total_downloads']}\n"
            f"{e_us} Activos: {stats_day['unique_users']}\n"
            f"{e_new} Nuevos: {stats_day['new_users']}\n\n"
            "<b>Este Mes:</b>\n"
            f"{e_dl} Descargas: {stats_month['total_downloads']}\n"
            f"{e_us} Activos: {stats_month['unique_users']}\n"
            f"{e_new} Nuevos: {stats_month['new_users']}\n\n"
            "<b>Este Año:</b>\n"
            f"{e_dl} Descargas: {stats_year['total_downloads']}\n"
            f"{e_us} Activos: {stats_year['unique_users']}\n\n"
            "<b>Histórico Total:</b>\n"
            f"{e_dl} Descargas: {stats_all['total_downloads']}\n"
            f"{e_new} Usuarios Totales: {stats_all['new_users']}\n"
        )

        # Intentar usar template si existe (opcional)
        text = base_summary
        if cms and cms.enabled:
            # Check if template exists before trying to use it to avoid errors if user hasn't added it yet
            # For now, we stick to the hardcoded enhanced format or update template later
            pass

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )
