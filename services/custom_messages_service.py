import logging
from typing import Any

from telegram import Bot

from repositories.custom_messages_repository import CustomMessagesRepository
from utils.template_parser import render_template
from utils.template_registry_data import TEMPLATE_REGISTRY

logger = logging.getLogger(__name__)


class CustomMessagesService:
    """
    Servicio para la lógica de negocio de CustomMessages.
    Desacopla el plugin (controlador) del repositorio y la lógica de renderizado.
    """

    def __init__(self, repository: CustomMessagesRepository, bot: Bot | None = None):
        self.repository = repository
        self.bot = bot
        self._global_vars_cache: dict[str, str] = {}

    async def initialize(self):
        """Inicializa el servicio cargando la caché."""
        await self.refresh_global_vars_cache()

    async def refresh_global_vars_cache(self):
        """Actualiza la caché de variables globales desde el repositorio."""
        self._global_vars_cache = await self.repository.get_all_global_vars()

    async def get_message(self, slug: str):
        """Recupera un mensaje de la BD."""
        return await self.repository.get_message(slug.lower())

    async def save_message(
        self, slug: str, chat_id: int, message_id: int, description: str | None = None, text_content: str | None = None
    ) -> bool:
        """Guarda un mensaje en la BD."""
        return await self.repository.save_message(slug.lower(), chat_id, message_id, description, text_content)

    async def delete_message(self, slug: str) -> bool:
        """Elimina un mensaje de la BD."""
        return await self.repository.delete_message(slug.lower())

    async def list_messages(self, limit: int = 100, offset: int = 0):
        """Lista mensajes personalizados."""
        return await self.repository.list_messages(limit, offset)

    async def set_setting(self, key: str, value: str) -> bool:
        """Guarda configuración en la BD."""
        return await self.repository.set_setting(key, value)

    async def get_setting(self, key: str) -> str | None:
        """Recupera configuración de la BD."""
        return await self.repository.get_setting(key)

    async def set_global_var(self, key: str, value: str) -> bool:
        """Define una variable global."""
        res = await self.repository.set_global_var(key, value)
        if res:
            await self.refresh_global_vars_cache()
        return res

    async def del_global_var(self, key: str) -> bool:
        """Elimina una variable global."""
        res = await self.repository.del_global_var(key)
        if res:
            await self.refresh_global_vars_cache()
        return res

    async def get_text(self, slug: str, default_text: str | None = None, user: Any = None, **replacements) -> str:
        """
        Recupera el texto de un mensaje guardado por su slug y lo renderiza.
        """
        msg = await self.get_message(slug)
        db_text = msg.text_content if msg else None

        bot_info = None
        if self.bot:
            bot_info = {
                "first_name": getattr(self.bot, "first_name", "Bot"),
                "username": getattr(self.bot, "username", "Bot"),
            }

        return await render_template(
            slug=slug,
            db_text=db_text,
            default_text=default_text,
            user=user,
            global_vars_cache=self._global_vars_cache,
            bot_info=bot_info,
            **replacements,
        )

    async def get_web_strings(self) -> dict[str, str]:
        """
        Recupera todos los strings destinados a la Mini App.
        """
        results = {}
        for slug in TEMPLATE_REGISTRY:
            if slug.startswith("web_"):
                text = await self.get_text(slug)
                # Remove prefix for shorter keys in JSON
                key = slug.replace("web_", "")
                results[key] = text
        return results
