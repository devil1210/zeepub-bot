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
                text_no = await cms.get_text("stats_no_users", Rol=target_level) if (cms and cms.enabled) else base_no
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text_no,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
                return

            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_header = f"📋 <b>Usuarios con nivel: {target_level.capitalize()}</b> ({len(users_list)})\n\n"
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
        from services.rich_message_service import RichMessageService

        # Obtener métricas paralelas
        stats_day = await get_stats_summary("day")
        stats_month = await get_stats_summary("month")
        stats_year = await get_stats_summary("year")
        stats_all = await get_stats_summary("all")

        blocks = [
            {
                "type": "heading",
                "size": 2,
                "text": "📊 Panel de Estadísticas • ZeePubs",
            },
            {
                "type": "paragraph",
                "text": "Resumen en tiempo real de actividad, descargas y crecimiento de la comunidad:",
            },
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": [
                    [
                        {"text": "📅 Periodo", "align": "left"},
                        {"text": "📥 Descargas", "align": "center"},
                        {"text": "👥 Activos", "align": "center"},
                        {"text": "🆕 Nuevos", "align": "center"},
                    ],
                    [
                        {"text": "Hoy", "align": "left"},
                        {"text": str(stats_day.get("total_downloads", 0)), "align": "center"},
                        {"text": str(stats_day.get("unique_users", 0)), "align": "center"},
                        {"text": str(stats_day.get("new_users", 0)), "align": "center"},
                    ],
                    [
                        {"text": "Este Mes", "align": "left"},
                        {"text": str(stats_month.get("total_downloads", 0)), "align": "center"},
                        {"text": str(stats_month.get("unique_users", 0)), "align": "center"},
                        {"text": str(stats_month.get("new_users", 0)), "align": "center"},
                    ],
                    [
                        {"text": "Este Año", "align": "left"},
                        {"text": str(stats_year.get("total_downloads", 0)), "align": "center"},
                        {"text": str(stats_year.get("unique_users", 0)), "align": "center"},
                        {"text": "—", "align": "center"},
                    ],
                    [
                        {"text": "Histórico Total", "align": "left"},
                        {"text": str(stats_all.get("total_downloads", 0)), "align": "center"},
                        {"text": "—", "align": "center"},
                        {"text": str(stats_all.get("new_users", 0)), "align": "center"},
                    ],
                ],
            },
        ]

        webapp_url = getattr(config, "WEBAPP_URL", None)
        action_buttons = [
            {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
            {"text": "🏠 Inicio", "callback_data": "volver_menu"},
        ]
        if webapp_url:
            action_buttons.insert(0, {"text": "🌐 Abrir ZeePub Web", "url": webapp_url})

        blocks.extend([
            {
                "type": "buttons",
                "align": "center",
                "buttons": action_buttons,
            },
            {"type": "divider"},
            {"type": "paragraph", "text": "#ZeePubs #Estadisticas"},
        ])

        res = await RichMessageService.send_rich_message(
            chat_id=update.effective_chat.id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

        if not res or not res.get("ok"):
            base_summary = (
                "📊 <b>Panel de Estadísticas</b>\n\n"
                f"• <b>Hoy:</b> {stats_day['total_downloads']} descargas | {stats_day['unique_users']} activos\n"
                f"• <b>Mes:</b> {stats_month['total_downloads']} descargas | {stats_month['unique_users']} activos\n"
                f"• <b>Total Histórico:</b> {stats_all['total_downloads']} descargas | {stats_all['new_users']} usuarios\n"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=base_summary,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
