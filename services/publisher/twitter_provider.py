import logging
from typing import Any

from services.publisher.base import PublisherProvider
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class TwitterPublisherProvider(PublisherProvider):
    TWITTER_TEMPLATE = (
        "📚 {serie} ║ {titulo}\n"
        "[?volumen]📖 Vol. {volumen}[/?]\n"
        "[?download_link]⬇️ {download_link}[/?]\n"
        "\n#{slug}"
    )

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        from services.cover_service import resolve_cover_data
        from services.publisher.twitter_publisher import post_to_twitter

        options = options or {}
        caption = options.get("caption")
        if not caption:
            caption = apply_publication_template(self.TWITTER_TEMPLATE, book_data)

        cover_source = (
            book_data.get("cover_high")
            or book_data.get("cover_original")
            or book_data.get("portada")
        )

        resolved_cover = (
            await resolve_cover_data(cover_source)
            if isinstance(cover_source, str)
            else cover_source
        )

        return await post_to_twitter(text_content=caption, cover_data=resolved_cover)
