# handlers/webapp_handlers.py

import json
import logging

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from config.config_settings import config
from core.state_manager import state_manager
from services.telegram_service import publicar_libro
from utils.security import validate_telegram_data

logger = logging.getLogger(__name__)


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data sent from the Mini App"""
    try:
        # Get the data sent from the Mini App
        web_app_data = update.effective_message.web_app_data.data
        data = json.loads(web_app_data)

        # Optional: Validate initData if present in the payload (Security Improvement)
        if "initData" in data:
            init_data_str = data["initData"]
            user_data = validate_telegram_data(init_data_str, config.TELEGRAM_TOKEN)
            if not user_data:
                logger.warning(f"⚠️ Invalid initData received from user {update.effective_user.id}")
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_text = "❌ Datos de autenticación inválidos."
                text = base_text
                if cms and cms.enabled:
                    text = await cms.get_text("webapp_auth_invalid")
                await update.message.reply_text(text)
                return
            # If valid, we can proceed (and maybe rely on user_data from initData instead of effective_user if needed)

        uid = update.effective_user.id
        state_manager.get_user_state(uid)

        logger.info(f"Received Mini App data from user {uid}: {data}")

        # Handle download action
        if data.get("action") == "download":
            book_title = data.get("title", "Libro")
            download_url = data.get("download_url")
            cover_url = data.get("cover_url", "")

            if not download_url:
                await update.message.reply_text("❌ No se encontró el enlace de descarga.")
                return

            # Send "Preparing..." message
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_text = "⏳ Preparando descarga..."
            text = base_text
            if cms and cms.enabled:
                text = await cms.get_text("download_preparing")
            prep_msg = await update.message.reply_text(text)
            menu_prep = (update.effective_chat.id, prep_msg.message_id)

            # Use the existing publicar_libro function
            await publicar_libro(
                update,
                context,
                uid,
                book_title,
                cover_url,
                download_url,
                menu_prep=menu_prep,
            )

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Mini App data: {e}")
        await update.message.reply_text("❌ Error al procesar los datos de la Mini App.")
    except Exception as e:
        logger.error(f"Error handling Mini App data: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error: {str(e)}")


def register_handlers(app):
    """Register Mini App handlers"""
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
