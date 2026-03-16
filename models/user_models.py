import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase

if TYPE_CHECKING:
    pass


class UserLevel(TimestampedBase):
    """
    V4 User Levels (Free, Premium, VIP, etc).
    """

    __tablename__ = "user_levels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Features
    daily_downloads: Mapped[int] = mapped_column(Integer, default=5)
    can_download: Mapped[bool] = mapped_column(default=True)
    can_read: Mapped[bool] = mapped_column(default=True)
    has_mini_app_access: Mapped[bool] = mapped_column(default=True)

    users: Mapped[list["User"]] = relationship(back_populates="level_info")


class User(TimestampedBase):
    """
    V4 User Entity.
    Strictly mapped User for Telegram interaction and Role-based access.
    """

    __tablename__ = "users"

    # Telegram ID is the PK (BigInteger to support Telegram IDs)
    telegram_id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, autoincrement=False)

    # Profile
    username: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="member")  # admin, member, guest

    # Access and UI configuration
    level_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_levels.id", ondelete="SET NULL"), index=True)
    ui_config: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Stats
    total_downloads: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    level_info: Mapped["UserLevel"] = relationship(back_populates="users")
    downloads: Mapped[list["DownloadLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class DownloadLog(TimestampedBase):
    """
    V4 Download Log.
    Tracks every book download per user.
    """

    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)

    book_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    downloaded_at: Mapped[any] = mapped_column(DateTime(timezone=True), server_default="now()")

    # Relationships
    user: Mapped["User"] = relationship(back_populates="downloads")


class AppTheme(TimestampedBase):
    """
    V4 Application Themes (Presets).
    """

    __tablename__ = "app_themes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    theme_type: Mapped[str] = mapped_column(String(20), default="dark")  # dark, light
    primary_color: Mapped[str] = mapped_column(String(20), default="#3b82f6")
    background_color: Mapped[str | None] = mapped_column(String(20))
    card_color: Mapped[str | None] = mapped_column(String(20))

    # Glassmorphism tokens
    glass_opacity: Mapped[float | None] = mapped_column(Float, default=0.6)
    nav_opacity: Mapped[float | None] = mapped_column(Float, default=0.8)
    accent_opacity: Mapped[float | None] = mapped_column(Float, default=1.0)
    glass_blur: Mapped[int | None] = mapped_column(Integer, default=12)
    card_glow_intensity: Mapped[float | None] = mapped_column(Float, default=0.5)

    # Layout configuration
    font_size: Mapped[int | None] = mapped_column(Integer, default=14)
    cover_width: Mapped[int | None] = mapped_column(Integer, default=120)
    banner_content_offset: Mapped[int | None] = mapped_column(Integer, default=0)
    border_width: Mapped[int | None] = mapped_column(Integer, default=1)
