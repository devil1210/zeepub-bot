import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class DeliveryProvider(ABC):
    @abstractmethod
    async def deliver_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        """
        Sends the book to the target.
        target_id: Destination (User ID, Chat ID, Email, etc.)
        book_data: Dictionary containing metadata and file location/bytes
        options: Additional parameters (thread_id, captions, etc.)
        """
        pass


class TelegramDeliveryProvider(DeliveryProvider):
    def __init__(self, bot=None):
        self.bot = bot

    async def deliver_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        from services.telegram_service import enviar_libro_directo

        if not self.bot:
            from api.main import bot as main_bot

            self.bot = main_bot.app.bot

        options = options or {}

        # Mapping generic book_data to what enviar_libro_directo expects
        return await enviar_libro_directo(
            bot=self.bot,
            user_id=int(target_id),
            title=book_data.get("title", "Libro"),
            download_url=book_data.get("filepath") or book_data.get("url"),
            target_chat_id=options.get("target_chat_id") or int(target_id),
            message_thread_id=options.get("message_thread_id"),
            metadata_override=book_data,
            explicit_file_buffer=book_data.get("epub_buffer") or book_data.get("file_buffer"),
            job_queue=options.get("job_queue"),
            auto_delete_seconds=options.get("auto_delete_seconds", 0),
        )


class DeliveryService:
    def __init__(self, default_provider: DeliveryProvider = None):
        self.providers = {"telegram": default_provider or TelegramDeliveryProvider()}

    def register_provider(self, name: str, provider: DeliveryProvider):
        self.providers[name] = provider

    async def deliver(
        self,
        platform: str,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        provider = self.providers.get(platform)
        if not provider:
            logger.error(f"Delivery provider for platform {platform} not found.")
            return False

        return await provider.deliver_book(target_id, book_data, options)


delivery_service = DeliveryService()
