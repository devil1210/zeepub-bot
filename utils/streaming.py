# utils/streaming.py

import logging

from telegram import Bot

logger = logging.getLogger(__name__)


async def send_message_draft(
    bot: Bot,
    chat_id: int,
    text: str,
    message_thread_id: int | None = None,
    parse_mode: str | None = "HTML",
):
    """
    Usa el método sendMessageDraft (API 9.3) para enviar un borrador de mensaje.
    Útil para mostrar progreso mientras se genera una respuesta larga.
    """
    try:
        # Usamos el request interno del bot para llamar al método no soportado aún oficialmente
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        if message_thread_id:
            payload["message_thread_id"] = message_thread_id
        if parse_mode:
            payload["parse_mode"] = parse_mode

        # En PTB v20+, bot.request.post es la forma de hacer peticiones raw
        # Dependiendo de la versión exacta de PTB, esto puede variar.
        # Probamos con el método genérico si existe.
        return await bot.do_api_request("sendMessageDraft", payload)
    except Exception as e:
        logger.error(f"Error en sendMessageDraft: {e}")
        return None
