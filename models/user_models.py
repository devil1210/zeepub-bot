import uuid
from datetime import datetime
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
    color: Mapped[str | None] = mapped_column(String(20))
    price: Mapped[float] = mapped_column(Float, default=0.0)

    # Features & Limits
    daily_downloads: Mapped[int] = mapped_column(Integer, default=5)
    can_download: Mapped[bool] = mapped_column(default=True)
    can_read: Mapped[bool] = mapped_column(default=True)
    has_mini_app_access: Mapped[bool] = mapped_column(default=True)
    early_access: Mapped[bool] = mapped_column(default=False)
    custom_themes: Mapped[bool] = mapped_column(default=False)
    allow_theme_templates: Mapped[bool] = mapped_column(default=True)
    show_recommendations: Mapped[bool] = mapped_column(default=True)
    can_upload_epub: Mapped[bool] = mapped_column(default=False)
    has_library_access: Mapped[bool] = mapped_column(default=True)
    can_request_books: Mapped[bool] = mapped_column(default=True)

    # UI Branding & Glassmorphism
    ui_theme: Mapped[str | None] = mapped_column(String(20), default="dark")
    ui_primary_color: Mapped[str | None] = mapped_column(String(20), default="#3b82f6")
    ui_font_size: Mapped[int | None] = mapped_column(Integer, default=14)
    ui_glass_blur: Mapped[int | None] = mapped_column(Integer, default=12)
    ui_nav_opacity: Mapped[int | None] = mapped_column(Integer, default=80)
    ui_accent_opacity: Mapped[int | None] = mapped_column(Integer, default=20)
    panel_transparency: Mapped[int | None] = mapped_column(Integer, default=60)
    background_color: Mapped[str | None] = mapped_column(String(20))
    card_color: Mapped[str | None] = mapped_column(String(20))
    force_settings: Mapped[bool] = mapped_column(default=False)
    border_radius: Mapped[int | None] = mapped_column(Integer, default=16)
    border_width: Mapped[int | None] = mapped_column(Integer, default=1)
    banner_content_offset: Mapped[int | None] = mapped_column(Integer, default=0)

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
    nickname: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default="member")  # admin, member, guest

    # Status & Flags
    is_active: Mapped[bool] = mapped_column(default=True)
    beta_tester: Mapped[bool] = mapped_column(default=False)
    bypass_limits: Mapped[bool] = mapped_column(default=False)
    has_library_access: Mapped[bool] = mapped_column(default=True)
    can_request_books: Mapped[bool] = mapped_column(default=True)
    can_upload_epub: Mapped[bool] = mapped_column(default=False)
    allow_theme_templates: Mapped[bool] = mapped_column(default=False)

    # Access and UI configuration
    level_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("user_levels.id", ondelete="SET NULL"), index=True)
    ui_settings: Mapped[dict | None] = mapped_column("ui_config", JSONB, default=dict)

    # Special Data
    roles: Mapped[list[str] | None] = mapped_column(JSONB, default=list)
    insignias: Mapped[list[str] | None] = mapped_column(JSONB, default=list)

    # Stats
    total_downloads: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)

    book_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

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
