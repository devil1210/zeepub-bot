# services/topic_service.py

import logging
from typing import Dict, Optional

from telegram import Bot

# from repositories.user_repository import user_repo (moved to methods)

logger = logging.getLogger(__name__)

TOPICS_SCHEMA = {
    "catalogo": "📂 Catálogo",
    "busquedas": "🔍 Búsquedas",
    "mis_libros": "📚 Mis Libros",
    "donaciones": "💎 Donaciones",
    "sistema": "⚙️ Sistema",
}


class TopicService:
    def __init__(self):
        pass

    async def ensure_topics(self, bot: Bot, user_id: int) -> Dict[str, int]:
        """
        Asegura que los tópicos existan para el usuario en su chat privado.
        Retorna un diccionario de {slug: message_thread_id}.
        """
        # En una implementación real, esto consultaría la DB para evitar recrear
        # o para recuperar IDs existentes.
        # Por ahora, simulamos el almacenamiento en el estado o DB.

        from repositories.user_repository import user_repo
        user_data = await user_repo.get_user_by_id(user_id)
        if not user_data:
            return {}

        settings = user_data.get("settings", {})
        topics = settings.get("topics", {})

        if topics:
            return topics

        # Si no hay tópicos, intentamos crearlos
        # Nota: Solo funciona si el usuario habilitó Forum Mode en el chat con el bot.
        new_topics = {}
        for slug, name in TOPICS_SCHEMA.items():
            try:
                # API 9.3: createForumTopic ahora funciona en private chats
                topic = await bot.create_forum_topic(chat_id=user_id, name=name)
                new_topics[slug] = topic.message_thread_id
            except Exception as e:
                logger.error(f"Error al crear tópico {slug} para {user_id}: {e}")
                # Si falla uno (ej. no habilitó foro), probablemente fallen todos.
                break

        if new_topics:
            settings["topics"] = new_topics
            await user_repo.update_user_settings(user_id, settings)

        return new_topics

    async def get_topic_id(self, user_id: int, slug: str) -> Optional[int]:
        """Recupera el thread_id para un slug específico."""
        from repositories.user_repository import user_repo
        user_data = await user_repo.get_user_by_id(user_id)
        if not user_data:
            return None
        return user_data.get("settings", {}).get("topics", {}).get(slug)


topic_service = TopicService()
