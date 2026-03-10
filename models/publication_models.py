from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase


class PublicationChannel(TimestampedBase):
    """
    V4 Publication Channels.
    Destinations like Telegram Channels, Facebook Groups, Webhooks.
    """

    __tablename__ = "publication_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # 'telegram', 'discord', 'webhook'
    target_id: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    config: Mapped[dict | None] = mapped_column(JSON)  # Extra configs (tokens, threads)

    # Relationships
    queued_items: Mapped[list["PublicationQueue"]] = relationship(
        back_populates="channel", cascade="all, delete-orphan"
    )


class PublicationTemplate(TimestampedBase):
    """
    V4 Publication Templates.
    Injectable HTML/Markdown templates for dynamic posting.
    """

    __tablename__ = "publication_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # The template string with {placeholders}
    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_config: Mapped[dict | None] = mapped_column(JSON)  # Layout preferences

    # Relationships
    queued_items: Mapped[list["PublicationQueue"]] = relationship(back_populates="template")


class PublicationQueue(TimestampedBase):
    """
    V4 Publication Queue for massive scheduling.
    """

    __tablename__ = "publication_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    channel_id: Mapped[int] = mapped_column(ForeignKey("publication_channels.id"), nullable=False)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("publication_templates.id"))

    # Scheduling
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, publishing, sent, failed

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Snapshot to avoid costly reads at publish time
    payload: Mapped[dict | None] = mapped_column(JSON)

    # Relationships
    channel: Mapped["PublicationChannel"] = relationship(back_populates="queued_items")
    template: Mapped[Optional["PublicationTemplate"]] = relationship(back_populates="queued_items")
