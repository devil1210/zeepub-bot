from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class PublicationChannel(Base):
    __tablename__ = "publication_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    platform: Mapped[str] = mapped_column(String(20))  # telegram, facebook
    target_id: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(default=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)


class PublicationTemplate(Base):
    __tablename__ = "publication_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(default=False)
    extra_config: Mapped[dict] = mapped_column(JSONB, default=dict)


class PublicationQueue(Base):
    __tablename__ = "publication_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("publication_channels.id"))
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("publication_templates.id"))

    scheduled_for: Mapped[datetime] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    published_at: Mapped[Optional[datetime]] = mapped_column()

    error_message: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB)
