from telegram import Update


def get_thread_id(update: Update) -> int | None:
    """
    Extrae el message_thread_id de un Update de Telegram de forma robusta.
    Retorna None si no hay thread_id (chat privado o grupo sin topics).
    """
    if not update:
        return None

    # 1. effective_message es el más confiable en python-telegram-bot
    eff = getattr(update, "effective_message", None)
    if eff:
        tid = getattr(eff, "message_thread_id", None)
        if tid is not None:
            return tid
        if getattr(eff, "is_topic_message", False):
            reply_to = getattr(eff, "reply_to_message", None)
            if reply_to:
                return getattr(reply_to, "message_thread_id", None) or getattr(reply_to, "message_id", None)

    # 2. Fallbacks directos
    if hasattr(update, "message") and update.message:
        tid = getattr(update.message, "message_thread_id", None)
        if tid is not None:
            return tid

    if hasattr(update, "callback_query") and update.callback_query:
        if hasattr(update.callback_query, "message") and update.callback_query.message:
            tid = getattr(update.callback_query.message, "message_thread_id", None)
            if tid is not None:
                return tid

    return None


def is_command_for_bot(update: Update, bot_username: str) -> bool:
    """
    Verifica si un comando está dirigido a este bot específicamente.
    """
    if not update or not hasattr(update, "message") or not update.message:
        return True

    # En chats privados, siempre es para este bot
    if update.effective_chat.type == "private":
        return True

    # Verificar si el mensaje tiene entidades de comando
    if not update.message.entities:
        return True

    # Buscar la entidad de bot_command
    for entity in update.message.entities:
        if entity.type == "bot_command":
            # Extraer el texto del comando
            command_text = update.message.text[entity.offset : entity.offset + entity.length]

            # Si el comando tiene @botusername, verificar que sea este bot
            if "@" in command_text:
                mentioned_bot = command_text.split("@")[1]
                return mentioned_bot.lower() == bot_username.lower()

            return True

    return True
