from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from .base import TimestampedBase


class UserLevel(TimestampedBase):
    """
    V4 User Levels (Free, Premium, VIP, etc).
    """

    __tablename__ = "user_levels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Features
    daily_downloads: Mapped[int] = mapped_column(Integer, default=5)
    can_download: Mapped[bool] = mapped_column(default=True)
    can_read: Mapped[bool] = mapped_column(default=True)
    has_mini_app_access: Mapped[bool] = mapped_column(default=True)
    has_library_access: Mapped[bool] = mapped_column(default=True)
    can_request_books: Mapped[bool] = mapped_column(default=True)
    can_upload_epub: Mapped[bool] = mapped_column(default=False)
    early_access: Mapped[bool] = mapped_column(default=False)
    custom_themes: Mapped[bool] = mapped_column(default=False)
    allow_theme_templates: Mapped[bool] = mapped_column(default=False)
    show_recommendations: Mapped[bool] = mapped_column(default=True)

    # Pricing (para stats/revenue)
    price: Mapped[float] = mapped_column(Float, default=0.0)

    # Visual
    color: Mapped[str | None] = mapped_column(String(20), default="#607D8B")
    ui_theme: Mapped[str | None] = mapped_column(String(50), default="dark")
    ui_primary_color: Mapped[str | None] = mapped_column(String(20))
    ui_nav_opacity: Mapped[int | None] = mapped_column(Integer)
    ui_font_size: Mapped[int | None] = mapped_column(Integer)
    ui_glass_blur: Mapped[int | None] = mapped_column(Integer)
    ui_cover_width: Mapped[int | None] = mapped_column(Integer)
    ui_accent_opacity: Mapped[int | None] = mapped_column(Integer)
    panel_transparency: Mapped[int | None] = mapped_column(Integer)
    background_color: Mapped[str | None] = mapped_column(String(20))
    card_color: Mapped[str | None] = mapped_column(String(20))
    banner_content_offset: Mapped[int | None] = mapped_column(Integer)
    force_settings: Mapped[bool] = mapped_column(default=False)

    users: Mapped[list["User"]] = relationship(back_populates="level_info")


class User(TimestampedBase):
    """
    V4 User Entity.
    Strictly mapped User for Telegram interaction and Role-based access.
    """

    __tablename__ = "users"

    # Telegram ID is the PK (BigInteger to support Telegram IDs)
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    # Profile
    username: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(255))

    # Access and UI configuration
    level_id: Mapped[int] = mapped_column(ForeignKey("user_levels.id", ondelete="SET DEFAULT"), default=6, index=True)
    role: Mapped[str] = mapped_column(String(50), default="user")  # admin, mod, user

    # Flexible structured settings
    ui_settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Roles / Badges from the agent ecosystem
    roles: Mapped[list | None] = mapped_column(JSONB, default=list)
    insignias: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Permissions overrides (User specific)
    has_library_access: Mapped[bool] = mapped_column(default=True)
    can_request_books: Mapped[bool] = mapped_column(default=True)
    can_upload_epub: Mapped[bool] = mapped_column(default=False)
    allow_theme_templates: Mapped[bool] = mapped_column(default=False)
    beta_tester: Mapped[bool] = mapped_column(default=False)
    bypass_limits: Mapped[bool] = mapped_column(default=False)

    # Expiration and External
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    photo_url: Mapped[str | None] = mapped_column(String(512))
    email: Mapped[str | None] = mapped_column(String(255))
    total_downloads: Mapped[int] = mapped_column(Integer, default=0)

    # Compatibility synonyms/properties
    settings = synonym("ui_settings")

    # Relationships
    level_info: Mapped["UserLevel"] = relationship(back_populates="users")
    downloads: Mapped[list["DownloadLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "name": self.name,
            "nickname": self.nickname,
            "role": self.role,
            "level_id": self.level_id,
        }


class DownloadLog(TimestampedBase):
    """
    V4 Download Log.
    Tracks every book download per user for rate limiting and audit.
    """

    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Who downloaded
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True
    )
    user_id = synonym("telegram_id")

    # What was downloaded (hash for immutability)
    book_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    series_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    book_title: Mapped[str | None] = mapped_column(String(512))

    # Context
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="downloads")


class AppTheme(TimestampedBase):
    """
    Temas globales de la aplicación (Presets).
    Tabla: app_themes
    """

    __tablename__ = "app_themes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    # Visual Properties
    theme_type: Mapped[str] = mapped_column(String(20), default="dark")  # 'theme' in frontend
    primary_color: Mapped[str | None] = mapped_column(String(20))
    background_color: Mapped[str | None] = mapped_column(String(20))
    card_color: Mapped[str | None] = mapped_column(String(20))

    # Opacities & Effects
    glass_opacity: Mapped[int | None] = mapped_column(Integer)
    nav_opacity: Mapped[int | None] = mapped_column(Integer)
    accent_opacity: Mapped[int | None] = mapped_column(Integer)
    glass_blur: Mapped[int | None] = mapped_column(Integer)
    card_glow_intensity: Mapped[int | None] = mapped_column(Integer)
    border_radius: Mapped[int | None] = mapped_column(Integer, default=24)
    border_width: Mapped[int | None] = mapped_column(Integer, default=1)

    # Layout
    font_size: Mapped[int | None] = mapped_column(Integer)
    cover_width: Mapped[int | None] = mapped_column(Integer)
    banner_content_offset: Mapped[int | None] = mapped_column(Integer)
