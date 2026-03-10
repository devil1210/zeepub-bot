"""
handlers/v4/status_handler.py
------------------------------
Maneja el comando /status.
Muestra el estado del usuario (nivel, descargas usadas, privilegios).
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandlerV4


class StatusHandlerV4(BaseHandlerV4):
    """
    /status — Muestra el nivel y privilegios del usuario.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = await self.ensure_user(update)
        uid = update.effective_user.id
        privs = await self.get_privileges(uid)

        text = self._build_status_text(user, privs)
        await self.reply(update, text)

    @staticmethod
    def _build_status_text(user: dict, privs: dict) -> str:
        name = user.get("nickname") or user.get("name") or "Usuario"
        is_admin = privs.get("is_admin", False)
        can_download = privs.get("can_download", False)
        daily_limit = privs.get("daily_limit", 0)

        lines = [
            f"👤 <b>Estado de {name}</b>\n",
            f"🎖️ <b>Rol:</b> {'Administrador' if is_admin else 'Lector'}",
            f"📥 <b>Descargas:</b> {'Ilimitadas' if daily_limit < 0 else f'{daily_limit}/día'}",
            f"✅ <b>Puede descargar:</b> {'Sí' if can_download else 'No'}",
        ]
        return "\n".join(lines)
