# handlers/commands/start_handler.py

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.library_ui_service import mostrar_menu_principal
from utils.helpers import get_thread_id

from .base_handler import BaseCommandHandler

logger = logging.getLogger(__name__)


class StartHandler(BaseCommandHandler):
    """
    Handle /start command - User initialization and welcome.
    Single Responsibility: User onboarding and state management.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start: initialize state; admin->evil, others->normal."""
        uid = update.effective_user.id

        # Capture message_thread_id for topic support
        thread_id = get_thread_id(update)

        # API 9.3: Support for topics in private chat
        bot_user_dict = update.effective_user.to_dict()
        has_topics = bot_user_dict.get("has_topics_enabled", False)

        if has_topics:
            from services.topic_service import topic_service

            # Ensure topics exist and get "System" topic ID for welcome
            topic_ids = await topic_service.ensure_topics(context.bot, uid)
            if topic_ids:
                # If topics exist, redirect welcome message to "System" topic
                thread_id = topic_ids.get("sistema", thread_id)

        # Check for deep-linking arguments (e.g. /start link_b64email or /start series_hash)
        if context.args and len(context.args) > 0:
            arg = context.args[0]
            if (
                arg.startswith("series_")
                or arg.startswith("serie_")
                or arg.startswith("show_series_")
            ):
                series_hash_short = arg.split("_")[-1]
                try:
                    from services.library_service import LibraryService
                    from services.library_ui_service import mostrar_volumenes_local

                    series_hash = await LibraryService.resolve_series_hash(
                        series_hash_short
                    )
                    if series_hash:
                        await mostrar_volumenes_local(
                            update, context, series_hash, force_new=True
                        )
                        return
                except Exception as e:
                    logger.error(f"Error procesando deep link de serie: {e}")

            if arg.startswith("auth_"):
                try:
                    from services.user_service import confirm_qr_auth_session
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

                    tg_user = update.effective_user
                    ok = await confirm_qr_auth_session(
                        token=arg,
                        telegram_id=uid,
                        telegram_username=tg_user.username,
                        first_name=tg_user.first_name,
                        bot=context.bot,
                    )
                    if ok:
                        text = (
                            f"🎉 <b>¡Vinculación Autorizada!</b>\n\n"
                            f"Hola <b>{tg_user.first_name}</b>, tu cuenta de Telegram (@{tg_user.username or uid}) "
                            f"ha sido autorizada y vinculada en tiempo real con tu navegador web.\n\n"
                            f"Ya puedes regresar a la pantalla de tu navegador."
                        )
                        reply_markup = InlineKeyboardMarkup([[
                            InlineKeyboardButton("🌐 Volver a ZeePub Web", url="https://zp-dev.sp-core.vip")
                        ]])
                        await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
                        return
                except Exception as e:
                    logger.error(f"Error procesando token QR auth: {e}")

            if arg.startswith("link_"):
                import base64
                encoded_email = arg[5:]
                try:
                    padded = encoded_email + "=" * (-len(encoded_email) % 4)
                    email = base64.urlsafe_b64decode(padded.encode()).decode("utf-8")
                    
                    from services.user_service import link_telegram_to_user
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

                    await link_telegram_to_user(
                        current_user_id=uid,
                        telegram_identifier=str(uid),
                        bot=context.bot
                    )

                    tg_user = update.effective_user
                    from repositories.user_repository import user_repo
                    await user_repo.update_profile(
                        uid,
                        username=tg_user.username,
                        first_name=tg_user.first_name,
                        last_name=tg_user.last_name,
                        email=email
                    )

                    text = (
                        f"🎉 <b>¡Cuenta de Telegram Vinculada!</b>\n\n"
                        f"Hola <b>{tg_user.first_name}</b>, tu cuenta de Telegram (@{tg_user.username or uid}) "
                        f"ha sido vinculada exitosamente con tu sesión web (<b>{email}</b>).\n\n"
                        f"Ya puedes volver a la web y disfrutar de tus descargas y beneficios."
                    )
                    reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🌐 Volver a ZeePub Web", url="https://zp-dev.sp-core.vip")
                    ]])
                    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
                    return
                except Exception as e:
                    logger.error(f"Error procesando deep link de vinculacion: {e}")

        # Clean previous temporary book state on restart
        self._clean_user_state(uid)

        await mostrar_menu_principal(update, context)
