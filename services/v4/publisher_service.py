"""
services/v4/publisher_service.py
----------------------------------
PublisherServiceV4: Orquestador central de publicaciones ZeePub.

V4 Architecture:
- UUID based entities.
- Full async compliance.
- Repository pattern (V4).
- Provider-based announcement system.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from repositories.v4.book_repository import BookRepository
from repositories.v4.publication_repository import (
    PublicationChannelRepository,
    PublicationQueueRepository,
)
from repositories.v4.series_repository import SeriesRepository

from .base_service import BaseService

if TYPE_CHECKING:
    from telegram.ext import Application

    from models.library_models import Book, Series
    from models.publication_models import PublicationQueue

# -----------------------------------------------------------------------------
# DTOs & Exceptions
# -----------------------------------------------------------------------------


@dataclass
class EnqueueResult:
    success: bool
    queue_ids: list[uuid.UUID] = field(default_factory=list)
    reason: str | None = None


@dataclass
class PublishResult:
    queue_id: uuid.UUID
    success: bool
    channel_name: str = ""
    error: str | None = None


class PublisherError(Exception):
    """Base error for publishing operations."""

    pass


# -----------------------------------------------------------------------------
# Default Templates
# -----------------------------------------------------------------------------

DEFAULT_TEMPLATES = {
    "telegram": (
        "📚 <b>{series_name}</b>\n"
        "🔖 <i>{title}</i>\n\n"
        "{description}\n\n"
        "📂 <b>Volumen:</b> {volume}\n"
        "✍️ <b>Hashtag:</b> #{slug}\n\n"
        "#ZeePubBot #V4"
    ),
    "facebook": ("📚 {series_name} - {title}\n\n{description}\n\nDescarga disponible en ZeePub Bot.\n#{slug} #ZeePub"),
}

# -----------------------------------------------------------------------------
# Providers
# -----------------------------------------------------------------------------


class BasePublisherProvider:
    """Interface for publishing providers."""

    async def announce_book(self, target_id: str, text: str, payload: dict, **kwargs) -> bool:
        raise NotImplementedError


class TelegramPublisherProvider(BasePublisherProvider):
    async def announce_book(self, target_id: str, text: str, payload: dict, **kwargs) -> bool:
        bot_app: Application = kwargs.get("bot_app")
        if not bot_app:
            return False

        cover_url = payload.get("cover_url")
        try:
            if cover_url:
                await bot_app.bot.send_photo(chat_id=target_id, photo=cover_url, caption=text, parse_mode="HTML")
            else:
                await bot_app.bot.send_message(chat_id=target_id, text=text, parse_mode="HTML")
            return True
        except Exception:
            # Fallback to text if photo fails
            try:
                await bot_app.bot.send_message(chat_id=target_id, text=text, parse_mode="HTML")
                return True
            except Exception:
                return False


class FacebookPublisherProvider(BasePublisherProvider):
    async def announce_book(self, target_id: str, text: str, payload: dict, **kwargs) -> bool:
        # Mocking FB for now as per V4 current state
        print(f"[MOCK FB] Posted to {target_id}: {text[:50]}...")
        return True


# -----------------------------------------------------------------------------
# Main Service
# -----------------------------------------------------------------------------


class PublisherServiceV4(BaseService):
    def __init__(self, db_manager):
        super().__init__(db_manager)
        self.providers = {"telegram": TelegramPublisherProvider(), "facebook": FacebookPublisherProvider()}

    async def enqueue_book(
        self,
        book_id: uuid.UUID,
        channel_ids: list[uuid.UUID] | None = None,
        scheduled_for: datetime | None = None,
        template_id: uuid.UUID | None = None,
    ) -> EnqueueResult:
        """Enqueues a book for publication in one or more channels."""
        from models.publication_models import PublicationQueue

        scheduled_for = scheduled_for or (datetime.now(UTC) + timedelta(seconds=30))

        async with self.db.get_session() as session:
            book_repo = BookRepository(session)
            book = await book_repo.get_by_id(book_id)
            if not book:
                return EnqueueResult(success=False, reason="book_not_found")

            # Load series for payload building
            series_repo = SeriesRepository(session)
            series = await series_repo.get_by_id(book.series_id)
            if not series:
                return EnqueueResult(success=False, reason="series_not_found")

            payload = self._build_payload(book, series)

            # Resolve channels
            channel_repo = PublicationChannelRepository(session)
            if channel_ids:
                channels = []
                for cid in channel_ids:
                    c = await channel_repo.get_by_id(cid)
                    if c and c.is_active:
                        channels.append(c)
            else:
                channels = await channel_repo.get_active_channels()

            if not channels:
                return EnqueueResult(success=False, reason="no_active_channels")

            queue_repo = PublicationQueueRepository(session)
            queue_ids = []

            for channel in channels:
                item = PublicationQueue(
                    book_id=book_id,
                    book_hash=book.hash,
                    channel_id=channel.id,
                    template_id=template_id,
                    scheduled_for=scheduled_for,
                    status="pending",
                    payload=payload,
                )
                created = await queue_repo.create(item)
                queue_ids.append(created.id)
                self.logger.info(f"[ENQUEUE V4] book={book.hash} -> channel={channel.name}")

            await session.commit()
            return EnqueueResult(success=True, queue_ids=queue_ids)

    async def process_queue(self, **kwargs) -> list[PublishResult]:
        """Processes pending queue items."""
        results = []
        async with self.db.get_session() as session:
            queue_repo = PublicationQueueRepository(session)
            pending = await queue_repo.get_pending_queue(limit=20)

            for item in pending:
                result = await self._process_item(item, queue_repo, **kwargs)
                await queue_repo.update(item)  # Ensure item status changes are persisted
                results.append(result)

            await session.commit()

        return results

    async def _process_item(self, item: PublicationQueue, repo: PublicationQueueRepository, **kwargs) -> PublishResult:
        item.status = "publishing"
        await repo.session.flush()

        channel = item.channel
        if not channel:
            item.status = "failed"
            item.error_message = "Channel details missing"
            return PublishResult(queue_id=item.id, success=False, error=item.error_message)

        platform = channel.platform.lower()
        provider = self.providers.get(platform)

        if not provider:
            item.status = "failed"
            item.error_message = f"Unsupported platform: {platform}"
            return PublishResult(queue_id=item.id, success=False, error=item.error_message)

        try:
            text = self._render_template(item)
            success = await provider.announce_book(channel.target_id, text, item.payload, **kwargs)

            if success:
                item.status = "sent"
                item.published_at = datetime.now(UTC)
                self.logger.info(f"[PUB V4 OK] queue_id={item.id} -> {channel.name}")
            else:
                item.status = "failed"
                item.error_message = f"Provider announcement failed for {platform}"

            return PublishResult(queue_id=item.id, success=success, channel_name=channel.name)

        except Exception as e:
            item.status = "failed"
            item.error_message = str(e)
            self.logger.error(f"[PUB V4 ERROR] queue_id={item.id}: {e}")
            return PublishResult(queue_id=item.id, success=False, error=str(e))

    def _render_template(self, item: PublicationQueue) -> str:
        payload = item.payload or {}
        platform = item.channel.platform.lower()

        template_content = DEFAULT_TEMPLATES.get(platform, DEFAULT_TEMPLATES["telegram"])
        if item.template and item.template.content:
            template_content = item.template.content

        try:
            return template_content.format_map(SafeDict(payload))
        except Exception:
            return f"📚 New Book: {payload.get('title', 'Untitled')}"

    @staticmethod
    def _build_payload(book: Book, series: Series) -> dict[str, Any]:
        """Snapshot of metadata for publication."""
        return {
            "title": book.title or series.title_raw,
            "series_name": series.title_spanish or series.title_raw,
            "description": series.description or "",
            "volume": str(book.volume_number),
            "slug": series.slug or "",
            "cover_url": series.cover_url or "",
            "hash": book.hash,
            "book_id": str(book.id),
        }


class SafeDict(dict):
    def __missing__(self, key):
        return f"[{key}]"
