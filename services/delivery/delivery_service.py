import logging
from typing import Any

logger = logging.getLogger(__name__)


class DeliveryProvider:
    async def deliver_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError


class TelegramDeliveryProvider(DeliveryProvider):
    def __init__(self, bot=None):
        self.bot = bot

    async def deliver_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        from repositories.publication_repository import pub_repo
        from services.publisher.publisher_service import TelegramPublisherProvider
        from services.telegram_service import enviar_libro_directo

        if not self.bot:
            from api.main import bot as main_bot

            self.bot = main_bot.app.bot

        options = options or {}

        # --- Lógica de Plantillas para Entrega Directa ---
        custom_caption = options.get("caption")
        caption_template = None

        if not custom_caption:
            try:
                # Obtener plantillas por defecto desde la base de datos
                templates = await pub_repo.get_templates(platform="telegram")

                cover_t = next((t for t in templates if (t.extra_config or {}).get("type") == "cover"), None)
                synopsis_t = next((t for t in templates if (t.extra_config or {}).get("type") == "synopsis"), None)
                info_t = next((t for t in templates if (t.extra_config or {}).get("type") == "info"), None)

                # Fallback a los defaults definidos en el Provider
                cover_content = cover_t.content if cover_t else TelegramPublisherProvider.COVER_TEMPLATE
                syn_content = synopsis_t.content if synopsis_t else TelegramPublisherProvider.SYNOPSIS_TEMPLATE
                info_content = info_t.content if info_t else TelegramPublisherProvider.INFO_TEMPLATE

                # Unir plantillas con separador <hr> para que enviar_libro_directo las aplique y divida
                caption_template = f"{cover_content}\n<hr>\n{syn_content}\n<hr>\n{info_content}"
                logger.info("Caption template construido para entrega directa.")
            except Exception as e:
                logger.warning(f"Error construyendo caption_template en deliver_book: {e}")

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
            custom_caption=custom_caption,
            caption_template=caption_template,
        )


class DeliveryService:
    def __init__(self, bot=None):
        self.providers = {
            "telegram": TelegramDeliveryProvider(bot),
        }

    async def deliver_book(
        self,
        provider_type: str,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        provider = self.providers.get(provider_type)
        if not provider:
            logger.error(f"Provider not found: {provider_type}")
            return False

        return await provider.deliver_book(target_id, book_data, options)


# Singleton instance for easy import
delivery_service = DeliveryService()
