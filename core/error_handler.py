import logging
import asyncio
from telegram import Update
from telegram.error import (
    TimedOut,
    NetworkError,
    BadRequest,
    Unauthorized,
    Forbidden,
    RetryAfter,
)
from config.config_settings import config

text_logger = logging.getLogger(__name__)


class ErrorHandler:
    """Manejo centralizado de errores del bot."""

    RETRY_ERRORS = (TimedOut, NetworkError)
    USER_ERRORS = (BadRequest, Unauthorized, Forbidden)

    @staticmethod
    async def handle_error(update, context):
        """Maneja errores de forma inteligente."""
        error = context.error

        # Errores recuperables - retry automático (simulado, ya que telegram.ext maneja retries internos,
        # pero esto es para loguear y evitar crash)
        if isinstance(error, ErrorHandler.RETRY_ERRORS):
            text_logger.warning(f"Error temporal: {error}")
            return

        # Rate limiting de Telegram
        if isinstance(error, RetryAfter):
            text_logger.warning(f"Rate limited, esperar {error.retry_after}s")
            await asyncio.sleep(error.retry_after)
            return

        # Errores de usuario - notificar si es posible
        if isinstance(error, ErrorHandler.USER_ERRORS):
            # Loguear advertencia pero no crash
            text_logger.warning(f"Error de usuario con update {update}: {error}")
            if update and getattr(update, "effective_message", None):
                try:
                    await update.effective_message.reply_text(
                        "❌ Error al procesar tu solicitud. Intenta nuevamente o contacta a soporte."
                    )
                except Exception:
                    pass  # Si no podemos responder, ignorar
            return

        # Errores críticos - logging completo
        text_logger.exception(f"Error crítico en update {update}: {error}")

        # Notificar a admins de errores críticos
        await ErrorHandler.notify_admins(context.bot, error, update)

    @staticmethod
    async def notify_admins(bot, error, update):
        """Notifica errores críticos a administradores."""
        error_msg = (
            f"🚨 <b>Error Crítico</b>\n\n"
            f"<code>{type(error).__name__}</code>\n"
            f"{str(error)[:500]}"
        )
        for admin_id in config.ADMIN_USERS:
            try:
                await bot.send_message(
                    chat_id=admin_id, text=error_msg, parse_mode="HTML"
                )
            except Exception:
                pass
