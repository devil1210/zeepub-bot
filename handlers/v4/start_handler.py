"""
handlers/v4/start_handler.py
------------------------------
Maneja el comando /start.
V4: Usa UserService para registrar al usuario antes de mostrar el menú.
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandlerV4


class StartHandlerV4(BaseHandlerV4):
    """
    /start — Bienvenida e inicialización de usuario.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        # 1. Auto-registro: garantiza que el usuario existe en la BD
        user = await self.ensure_user(update)
        uid = update.effective_user.id

        # 2. Obtener privilegios para personalizar el mensaje
        privs = await self.get_privileges(uid)

        # 3. Construir mensaje de bienvenida
        text = self._build_welcome_text(user, privs)

        await self.reply(update, text)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _build_welcome_text(user: dict, privs: dict) -> str:
        name = user.get("nickname") or user.get("name") or "lector"
        is_admin = privs.get("is_admin", False)

        if is_admin:
            return (
                f"🔧 <b>Modo Administrador</b>\n\n"
                f"Hola, <b>{name}</b>.\n\n"
                f"• /catalog — Catálogo\n"
                f"• /search — Buscar\n"
                f"• /status — Estado\n"
            )

        return (
            f"📚 <b>Bienvenido a ZeePub, {name}</b>\n\n"
            f"Tu biblioteca personal de novelas ligeras.\n\n"
            f"<b>Comandos disponibles:</b>\n"
            f"• /catalog — Explorar catálogo\n"
            f"• /search — Buscar títulos\n"
            f"• /status — Ver tu estado\n\n"
            f"💡 <i>Usa la Mini App para explorar, leer y descargar.</i>"
        )
