import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.v4.base import BaseHandlerV4, with_services

logger = logging.getLogger(__name__)


class StartHandlerV4(BaseHandlerV4):
    """
    Handler v4.0 para el comando /start.
    Responsable del onboarding y sincronización inicial de usuario.
    """

    @with_services
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        user_service = services["user_service"]
        uid = update.effective_user.id

        # 1. Obtener o crear usuario asíncronamente
        user = await user_service.get_or_create_user(
            telegram_id=uid, username=update.effective_user.username, full_name=update.effective_user.full_name
        )

        # 2. Inicializar estado
        st = self.get_user_state(uid)
        st["historial"] = []

        # 3. UI Premium (Glassmorphism design tokens)
        welcome_text = (
            f"🚀 <b>Hola, {user.full_name}!</b>\n\n"
            f"Bienvenido a la nueva arquitectura <b>ZeePub v4.0</b>.\n"
            f"Estado: <code>{user.level.name}</code>\n\n"
            f"📖 <b>Acceso Rápido:</b>\n"
            f"• /catalog - Catálogo de series\n"
            f"• /search - Buscar novelas\n"
            f"• /status - Mi perfil y descargas\n\n"
            f"<i>Desarrollado con arquitectura Handler-Service-Repository.</i>"
        )

        keyboard = [
            [InlineKeyboardButton("📚 Explorar Catálogo", callback_data="catalog|0")],
            [InlineKeyboardButton("🔍 Buscar Libro", callback_data="search_init")],
            [InlineKeyboardButton("⚙️ Ajustes", callback_data="settings_menu")],
        ]

        await self.send_glass_message(update, welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))
