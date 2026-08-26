from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class PublicationChannel(Base):
    """
    Canales o destinos de publicación (Telegram Channels, Facebook Groups, etc.)
    """

    __tablename__ = "publication_channels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    platform: Mapped[str] = mapped_column(String(20))  # telegram, facebook
    target_id: Mapped[str] = mapped_column(String(100))  # @ZeePubs o ID numérico
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relación con la cola
    queued_items = relationship("PublicationQueue", back_populates="channel", cascade="all, delete-orphan")


class DiscoveredChat(Base):
    """
    Chats descubiertos automáticamente por el bot (candidatos a canales).
    """

    __tablename__ = "discovered_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(50))  # group, supergroup, channel
    member_count: Mapped[int] = mapped_column(default=0)
    username: Mapped[str | None] = mapped_column(String(100))

    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PublicationTemplate(Base):
    """
    Plantillas de texto para las publicaciones.
    """

    __tablename__ = "publication_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    platform: Mapped[str] = mapped_column(String(20), default="telegram")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relación con la cola
    queued_items = relationship("PublicationQueue", back_populates="template")


class PublicationQueue(Base):
    """
    Cola de publicaciones programadas o enviadas.
    """

    __tablename__ = "publication_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_hash: Mapped[str] = mapped_column(ForeignKey("books.id"), index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("publication_channels.id"))
    template_id: Mapped[int | None] = mapped_column(ForeignKey("publication_templates.id"), nullable=True)

    scheduled_for: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    error_message: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    channel = relationship("PublicationChannel", back_populates="queued_items")
    template = relationship("PublicationTemplate", back_populates="queued_items")


class BookPublication(Base):
    """
    Registro histórico de publicaciones realizadas por libro en distintas plataformas (Facebook, Telegram, etc.)
    Permite saber cuántas veces se ha publicado un EPUB, en qué fechas y acceder al enlace directo del post.
    """

    __tablename__ = "book_publications"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(50), default="facebook", index=True)  # facebook, telegram
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("publication_channels.id", ondelete="SET NULL"), nullable=True)

    post_id: Mapped[str] = mapped_column(String(128), index=True)
    post_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    channel = relationship("PublicationChannel")
    book = relationship("Book", back_populates="publications")

