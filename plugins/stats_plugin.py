import logging
import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id
from services.user_service import get_effective_user, get_users_by_role
from services.stats_service import get_daily_stats
from datetime import datetime
from dateutil import parser as date_parser

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
        user_info = get_effective_user(uid)
        role = user_info.get("role", "free")
        is_admin = role == "admin" or uid in config.ADMIN_USERS
        if not is_admin and role != "staff":
            return

        thread_id = get_thread_id(update)

        # Modo Listar Usuarios por Rol: /stats premium
        if context.args:
            target_role = context.args[0].lower()
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

        # Modo Resumen Diario
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
