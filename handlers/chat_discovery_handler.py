import logging

from telegram import Update
from telegram.ext import ContextTypes

from repositories.publication_repository import pub_repo

logger = logging.getLogger(__name__)


async def chat_discovery_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Monitor pasivo que registra chats (grupos/canales) donde el bot está presente.
    """
    chat = None

    # Caso 1: Actualización de estado del bot en un chat (Added/Removed/Promoted)
    if update.my_chat_member:
        chat = update.my_chat_member.chat
        new_status = update.my_chat_member.new_chat_member.status

        # Si el bot fue expulsado, quizás deberíamos marcarlo,
        # pero por ahora save_discovered_chat solo hace upsert de info.
        # Si abandonó, no importa, sigue en historial "descubierto".

    # Caso 2: Mensaje en grupo/canal
    elif update.message and update.message.chat.type in ["group", "supergroup", "channel"]:
        chat = update.message.chat

    elif update.channel_post:
        chat = update.channel_post.chat

    if chat:
        try:
            # Filtrar chats privados
            if chat.type == "private":
                return

            member_count = 0
            try:
                member_count = await chat.get_member_count()
            except Exception:
                pass

            await pub_repo.save_discovered_chat(
                chat_id=str(chat.id),
                title=chat.title or "Sin Título",
                chat_type=chat.type,
                username=chat.username,
                member_count=member_count,
            )
            # logger.debug(f"Chat Discovered/Updated: {chat.title} ({chat.id})")
        except Exception as e:
            logger.error(f"Error in chat_discovery_handler: {e}")
