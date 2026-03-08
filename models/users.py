from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class User(Base):
    """
    Modelo unificado de Usuarios.
    """

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(255))
    photo_url: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)

    level_id: Mapped[int] = mapped_column(ForeignKey("user_levels.id"), default=6)
    role: Mapped[str] = mapped_column(String(50), default="user")

    is_beta: Mapped[bool] = mapped_column(Boolean, default=False)
    can_upload: Mapped[bool] = mapped_column(Boolean, default=False)
    can_upload_epub: Mapped[bool] = mapped_column(Boolean, default=False)

    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    level: Mapped["UserLevel"] = relationship(back_populates="users")
    ui_settings: Mapped["UserUISettings"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class UserLevel(Base):
    __tablename__ = "user_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    priority: Mapped[int] = mapped_column(default=0)
    color: Mapped[str] = mapped_column(String(20), default="#607D8B")
    price: Mapped[int] = mapped_column(Integer, default=0)

    # Permisos
    daily_limit: Mapped[int] = mapped_column(Integer, default=5)

    @hybrid_property
    def daily_downloads(self) -> int:
        return self.daily_limit

    @daily_downloads.setter
    def daily_downloads(self, value: int):
        self.daily_limit = value

    can_download: Mapped[bool] = mapped_column(Boolean, default=True)
    can_read: Mapped[bool] = mapped_column(Boolean, default=True)
    has_library_access: Mapped[bool] = mapped_column(Boolean, default=True)
    can_request_books: Mapped[bool] = mapped_column(Boolean, default=True)
    can_upload_epub: Mapped[bool] = mapped_column(Boolean, default=False)
    early_access: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_themes: Mapped[bool] = mapped_column(Boolean, default=False)
    has_mini_app_access: Mapped[bool] = mapped_column(Boolean, default=True)

    # UI Default Settings
    ui_theme: Mapped[str] = mapped_column(String(20), default="dark")
    ui_font_size: Mapped[int] = mapped_column(Integer, default=14)
    ui_glass_blur: Mapped[int] = mapped_column(Integer, default=12)
    ui_cover_width: Mapped[int] = mapped_column(Integer, default=120)
    ui_accent_opacity: Mapped[int] = mapped_column(Integer, default=20)
    panel_transparency: Mapped[int] = mapped_column(Integer, default=60)
    background_color: Mapped[str] = mapped_column(String(20), default="#0f172a")
    card_color: Mapped[str] = mapped_column(String(20), default="#1e293b")
    banner_content_offset: Mapped[int] = mapped_column(Integer, default=0)
    show_recommendations: Mapped[bool] = mapped_column(Boolean, default=True)
    force_settings: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_theme_templates: Mapped[bool] = mapped_column(Boolean, default=False)
    default_theme_id: Mapped[int | None] = mapped_column(Integer, default=None)

    users: Mapped[list[User]] = relationship(back_populates="level")


class UserUISettings(Base):
    """
    Configuración de UI (Glassmorphism tokens) específica del usuario.
    """

    __tablename__ = "user_ui_settings"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), primary_key=True)

    theme: Mapped[str] = mapped_column(String(20), default="dark")
    primary_color: Mapped[str] = mapped_column(String(20))
    glass_blur: Mapped[int] = mapped_column(Integer, default=12)
    glass_opacity: Mapped[int] = mapped_column(Integer, default=60)

    user: Mapped[User] = relationship(back_populates="ui_settings")


class AppTheme(Base):
    """
    Temas globales de la aplicación (Presets).
    """

    __tablename__ = "app_themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(String(500))

    # Visual Properties
    theme_type: Mapped[str] = mapped_column(String(20), default="dark")
    primary_color: Mapped[str | None] = mapped_column(String(20))
    background_color: Mapped[str | None] = mapped_column(String(20))
    card_color: Mapped[str | None] = mapped_column(String(20))

    # Opacities & Effects
    glass_opacity: Mapped[int | None] = mapped_column(Integer)
    nav_opacity: Mapped[int | None] = mapped_column(Integer)
    accent_opacity: Mapped[int | None] = mapped_column(Integer)
    glass_blur: Mapped[int | None] = mapped_column(Integer)
    card_glow_intensity: Mapped[int | None] = mapped_column(Integer)
    border_radius: Mapped[int] = mapped_column(Integer, default=24)
    border_width: Mapped[int] = mapped_column(Integer, default=1)

    # Layout
    font_size: Mapped[int | None] = mapped_column(Integer)
    cover_width: Mapped[int | None] = mapped_column(Integer)
    banner_content_offset: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
