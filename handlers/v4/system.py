import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config.config_settings import config
from handlers.v4.base import BaseHandlerV4, with_services
from utils.helpers import get_version_string

logger = logging.getLogger(__name__)


class SystemHandlerV4(BaseHandlerV4):
    """
    Handler v4.0 para comandos del sistema y utilidades.
    Gestiona /status, /cancel, /plugins, /evil, /changeweb, /acceso_web.
    """

    @with_services
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Handle /status: informa estado interno y nivel de usuario."""
        user_service = services["user_service"]
        uid = update.effective_user.id
        target_user = update.effective_user

        # Lógica para administradores: si citan un mensaje, mostrar status de ese usuario
        if update.message and update.message.reply_to_message:
            if uid in config.ADMIN_USERS:
                target_user = update.message.reply_to_message.from_user
                uid = target_user.id
                logger.info(f"Admin {update.effective_user.id} solicitó status para {uid}")

        user = await user_service.get_or_create_user(
            telegram_id=uid, username=target_user.username, full_name=target_user.full_name
        )

        level_name = user.level.name if user.level else "Desconocido"

        # UI Premium (Glassmorphism inspired)
        version = get_version_string()

        status_text = (
            f"📊 <b>Estado de Usuario</b>\n\n"
            f"👤 <b>Nombre:</b> {user.full_name}\n"
            f"🆔 <b>ID:</b> <code>{user.telegram_id}</code>\n"
            f"⭐ <b>Nivel:</b> <code>{level_name}</code>\n"
            f"🤖 <b>Versión:</b> {version}\n\n"
            f"<i>Descargas diarias y límites se gestionan dinámicamente según tu nivel.</i>"
        )

        keyboard = [
            [InlineKeyboardButton("⚙️ Mis Ajustes", callback_data="settings_menu")],
            [InlineKeyboardButton("🌐 Acceso Web", callback_data="web_access")],
        ]

        await self.send_glass_message(update, status_text, reply_markup=InlineKeyboardMarkup(keyboard))

    @with_services
    async def handle_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Handle /cancel: limpia estado y confirma cancelación."""
        uid = update.effective_user.id
        st = self.get_user_state(uid)

        # Limpiar flags de espera
        keys_to_clear = [k for k in st.keys() if k.startswith("esperando_") or k in ("series_id", "volume_id")]
        for key in keys_to_clear:
            st.pop(key, None)

        # Borrar el mensaje del comando si es posible
        try:
            await update.message.delete()
        except Exception:
            pass

        await self.send_glass_message(update, "✅ <b>Operación cancelada.</b>")

    @with_services
    async def handle_evil(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Handle /evil: placeholder para modo privado o administrativo."""
        uid = update.effective_user.id
        if uid not in config.ADMIN_USERS:
            return

        st = self.get_user_state(uid)
        st["esperando_password"] = True

        await self.send_glass_message(update, "🔒 <b>Modo Privado.</b> Por favor, ingresa la contraseña:")

    @with_services
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Maneja mensajes de texto generales basándose en el estado (esperando_...)."""
        if not update.message or not update.message.text:
            return

        uid = update.effective_user.id
        st = self.get_user_state(uid)
        text = update.message.text.strip()

        # 1. Esperando Búsqueda
        if st.get("esperando_busqueda"):
            st.pop("esperando_busqueda", None)
            from handlers.v4.search import SearchHandlerV4

            search_h = SearchHandlerV4(self.app)
            return await search_h.handle(update, context, query_text=text)

        # 2. Esperando Destino Manual
        if st.get("esperando_destino_manual"):
            st["destino"] = text
            st.pop("esperando_destino_manual", None)
            await self.send_glass_message(update, f"✅ <b>Destino manual establecido:</b> <code>{text}</code>")
            # Mostrar menú principal tras configurar
            from services.v4.ui_service import UIServiceV4

            text_menu, markup = await UIServiceV4.render_main_menu()
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=text_menu, reply_markup=markup, parse_mode="HTML"
            )
            return

        # 3. Esperando Password (Modo Evil)
        if st.get("esperando_password"):
            st.pop("esperando_password", None)
            if text == config.get_six_hour_password():
                await self.send_glass_message(update, "🔓 <b>Acceso concedido al Modo Evil.</b>")
            else:
                await self.send_glass_message(update, "❌ <b>Contraseña incorrecta.</b>")
            return

        # Si no hay estado de espera, ignorar o loguear (evitar spam)
        logger.debug(f"Mensaje ignorado de {uid}: {text}")

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE, **services):
        """Implementación requerida por BaseHandlerV4 (no se usa directamente si registramos por método)."""
        pass
