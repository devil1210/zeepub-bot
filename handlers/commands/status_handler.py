# handlers/commands/status_handler.py

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config.config_settings import config
from services.library_ui import build_status_rich_blocks
from services.rich_message_service import RichMessageService
from utils.download_limiter import downloads_left
from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class StatusHandler(BaseCommandHandler):
    """
    Handle /status command - Muestra el estado del usuario con Rich Message y Glass UI.
    Single Responsibility: Información de cuenta, cuota y estado del usuario.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status: informa perfil, rol, cuota y accesos rápidos."""
        uid = update.effective_user.id
        thread_id = get_thread_id(update)
        user_info = await self._get_user_info(update)

        user_name = update.effective_user.first_name or "Lector"
        level = user_info.get("level", "free")
        role = user_info.get("role")
        is_admin = user_info.get("is_real_admin", False) or uid in getattr(config, "ADMIN_USERS", [])

        if is_admin:
            user_rank = "👑 Administrador"
        elif level == "staff" or role == "Publicador":
            user_rank = "🎯 Staff / Publicador"
        elif level == "premium":
            user_rank = "💎 Premium"
        elif level == "vip":
            user_rank = "⭐ VIP"
        elif level == "whitelist":
            user_rank = "🤍 Whitelist"
        else:
            user_rank = "📖 Lector Regular"

        downloads_info = await downloads_left(uid)
        if downloads_info == "ilimitadas":
            downloads_str = "♾️ Ilimitadas"
        elif isinstance(downloads_info, int):
            downloads_str = f"{downloads_info} restantes"
        else:
            downloads_str = str(downloads_info)

        joined_date = user_info.get("joined_date") or user_info.get("created_at") or "Registrado"
        if isinstance(joined_date, datetime):
            joined_date_str = joined_date.strftime("%d/%m/%Y")
        else:
            joined_date_str = str(joined_date)

        last_download = user_info.get("last_download")
        if isinstance(last_download, datetime):
            last_download_str = last_download.strftime("%d/%m/%Y %H:%M")
        else:
            last_download_str = str(last_download) if last_download else "Sin descargas recientes"

        webapp_url = getattr(config, "WEBAPP_URL", None)

        blocks = build_status_rich_blocks(
            user_name=user_name,
            user_id=uid,
            user_rank=user_rank,
            downloads_str=downloads_str,
            joined_date=joined_date_str,
            last_download_str=last_download_str,
            webapp_url=webapp_url,
        )

        res = await RichMessageService.send_rich_message(
            chat_id=update.effective_chat.id,
            blocks=blocks,
            message_thread_id=thread_id,
        )

        if not res or not res.get("ok"):
            fallback_text = (
                f"👤 <b>Perfil de Lector • ZeePubs</b>\n\n"
                f"• <b>Usuario:</b> {user_name} (<code>{uid}</code>)\n"
                f"• <b>Rango:</b> {user_rank}\n"
                f"• <b>Cuota hoy:</b> {downloads_str}\n"
                f"• <b>Miembro desde:</b> {joined_date_str}\n"
                f"• <b>Última descarga:</b> {last_download_str}\n"
            )
            await self._send_message(update, fallback_text, thread_id)

