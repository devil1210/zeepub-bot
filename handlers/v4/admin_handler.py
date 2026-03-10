"""
handlers/v4/admin_handler.py
-----------------------------
Maneja comandos de administración (/admin).
V4: Verifica privilegios via UserService antes de ejecutar cualquier acción.
"""

from telegram import Update
from telegram.ext import ContextTypes

from .base_handler import BaseHandlerV4


class AdminHandlerV4(BaseHandlerV4):
    """
    /admin — Panel de administración (requiere is_admin).
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.ensure_user(update)
        uid = update.effective_user.id
        privs = await self.get_privileges(uid)

        if not privs.get("is_admin", False):
            await self.reply(update, "🔒 <b>Acceso denegado.</b> Este comando es solo para administradores.")
            return

        subcmd = (context.args[0].lower() if context.args else "").strip()

        if subcmd == "status":
            await self.reply(
                update, "🔧 <b>Admin Panel</b>\n\n✅ Sistema operativo.\nUsa la Mini App para gestión completa."
            )
        else:
            await self.reply(
                update,
                "🔧 <b>Panel de Administración V4</b>\n\n"
                "Comandos disponibles:\n"
                "• <code>/admin status</code> — Estado del sistema\n\n"
                "💡 Usa la Mini App para gestión avanzada.",
            )
