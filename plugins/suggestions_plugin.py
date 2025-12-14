import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from plugins.base_plugin import BasePlugin
from config.config_settings import config
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


class SuggestionsPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "suggestions_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Permite a los usuarios enviar sugerencias a los administradores."

    async def initialize(self, bot_instance) -> bool:
        try:
            bot_instance.add_handler(
                CommandHandler("sugerencia", self.sugerencia_command)
            )
            logger.info("Plugin Sugerencias: Handler /sugerencia registrado.")
            return True
        except Exception as e:
            logger.error(f"Error registrando plugin sugerencias: {e}")
            return False

    async def cleanup(self) -> None:
        pass

    async def sugerencia_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
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

        for admin_id in config.ADMIN_USERS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id, text=admin_msg, parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"No se pudo enviar sugerencia al admin {admin_id}: {e}")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ ¡Gracias! Tu sugerencia ha sido enviada a los administradores.",
            message_thread_id=thread_id,
        )
