import logging

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from config.config_settings import config
from plugins.base_plugin import BasePlugin
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class SuggestionsPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "suggestions_plugin"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Permite a los usuarios enviar sugerencias a los administradores."

    async def initialize(self, bot_instance) -> bool:
        try:
            from telegram.ext import CallbackQueryHandler

            bot_instance.add_handler(CommandHandler("sugerencia", self.sugerencia_command))
            bot_instance.add_handler(
                CallbackQueryHandler(self.suggestion_callback, pattern="^suggestion\\|")
            )
            logger.info("Plugin Sugerencias: Handler /sugerencia registrado.")
            return True
        except Exception as e:
            logger.error(f"Error registrando plugin sugerencias: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def sugerencia_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        thread_id = get_thread_id(update)

        if not context.args:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="ℹ️ Uso: `/sugerencia <tu mensaje>`\nEjemplo: `/sugerencia Agregar libros de fantasía`",
                parse_mode="Markdown",
                message_thread_id=thread_id,
            )
            return

        suggestion_text = " ".join(context.args)
        user_name = update.effective_user.first_name
        if update.effective_user.username:
            user_name += f" (@{update.effective_user.username})"

        admin_msg = (
            f"💡 <b>Nueva Sugerencia</b>\n\n"
            f"👤 <b>De:</b> {user_name} (<code>{uid}</code>)\n"
            f"📝 <b>Mensaje:</b>\n{suggestion_text}"
        )

        # Create interactive buttons for admins to respond
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = [
            [
                InlineKeyboardButton("✅ Aceptar", callback_data=f"suggestion|accept|{uid}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"suggestion|reject|{uid}"),
            ],
            [
                InlineKeyboardButton(
                    "💬 Respuesta Personalizada",
                    callback_data=f"suggestion|custom|{uid}",
                )
            ],
        ]

        for admin_id in config.ADMIN_USERS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=admin_msg,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            except Exception as e:
                logger.warning(f"No se pudo enviar sugerencia al admin {admin_id}: {e}")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ ¡Gracias! Tu sugerencia ha sido enviada a los administradores.",
            message_thread_id=thread_id,
        )

    async def suggestion_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks on suggestion messages."""
        query = update.callback_query
        await query.answer()

        data = query.data  # Format: "suggestion|action|user_id"
        _, action, user_id_str = data.split("|")
        user_id = int(user_id_str)

        cms = context.application.plugin_manager.get_plugin("custom_messages")

        if action == "accept":
            base_text = "✅ Sugerencia Aceptada\n\n¡Gracias por tu aporte! Tu sugerencia será tomada en cuenta."
            text = base_text
            if cms and cms.enabled:
                text = await cms.get_text("suggestion_accepted")

            try:
                await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
                await query.edit_message_text(
                    text=query.message.text + "\n\n✅ <b>Aceptada y notificada</b>",
                    parse_mode="HTML",
                )
            except Exception as e:
                await query.edit_message_text(
                    text=query.message.text + f"\n\n❌ Error: {e}", parse_mode="HTML"
                )

        elif action == "reject":
            base_text = "❌ Sugerencia Rechazada\n\nGracias por tu interés, pero tu sugerencia no será implementada en este momento."
            text = base_text
            if cms and cms.enabled:
                text = await cms.get_text("suggestion_rejected")

            try:
                await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
                await query.edit_message_text(
                    text=query.message.text + "\n\n❌ <b>Rechazada y notificada</b>",
                    parse_mode="HTML",
                )
            except Exception as e:
                await query.edit_message_text(
                    text=query.message.text + f"\n\n❌ Error: {e}", parse_mode="HTML"
                )

        elif action == "custom":
            # Activate custom response mode
            from core.state_manager import state_manager

            st = state_manager.get_user_state(update.effective_user.id)
            st["waiting_for_suggestion_response"] = user_id
            st["suggestion_original_message_id"] = query.message.message_id
            st["suggestion_original_chat_id"] = query.message.chat_id
            st["suggestion_original_text"] = query.message.text

            await query.edit_message_reply_markup(reply_markup=None)
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="✍️ Escribe tu respuesta personalizada (envía tu mensaje):",
            )
