from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .library_models import Book


class PublicationChannel(TimestampedBase):
    """
    V4 Publication Channels.
    Destinations like Telegram Channels, Facebook Groups, Webhooks.
    """

    __tablename__ = "publication_channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # 'telegram', 'facebook', 'discord', 'webhook'
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict | None] = mapped_column(JSONB)  # Extra configs (tokens, threads)

    # Relationships
    queued_items: Mapped[list[PublicationQueue]] = relationship(back_populates="channel", cascade="all, delete-orphan")


class DiscoveredChat(TimestampedBase):
    """
    Temporary storage for chats where the bot is present.
    Admins can promote these to PublicationChannel.
    """

    __tablename__ = "discovered_chats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str | None] = mapped_column(String(50))
    member_count: Mapped[int] = mapped_column(default=0)
    username: Mapped[str | None] = mapped_column(String(100))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PublicationTemplate(TimestampedBase):
    """
    V4 Publication Templates.
    Injectable HTML/Markdown templates for dynamic posting.
    """

    __tablename__ = "publication_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # The template string with {placeholders}
    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_config: Mapped[dict | None] = mapped_column(JSONB)  # Layout preferences

    # Relationships
    queued_items: Mapped[list[PublicationQueue]] = relationship(back_populates="template")


class PublicationQueue(TimestampedBase):
    """
    V4 Publication Queue for massive scheduling.
    """

    __tablename__ = "publication_queue"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True
    )
    book_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publication_channels.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publication_templates.id", ondelete="SET NULL")
    )

    # Scheduling
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, publishing, sent, failed

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Snapshot to avoid costly reads at publish time
    payload: Mapped[dict | None] = mapped_column(JSONB)

    # Relationships
    channel: Mapped[PublicationChannel] = relationship(back_populates="queued_items")
    template: Mapped[PublicationTemplate | None] = relationship(back_populates="queued_items")
    book: Mapped["Book"] = relationship("Book")
