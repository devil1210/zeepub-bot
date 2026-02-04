# sqlalchemy models for user management
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """
    Representa un usuario del bot (Telegram).
    Espejo de la tabla 'users' en Supabase.
    """

    __tablename__ = "users"

    # Telegram ID es la PK (BigInteger para soportar IDs de Telegram)
    telegram_id = Column(BigInteger, primary_key=True, autoincrement=False)

    # Perfil
    username = Column(String(255))
    name = Column(String(255))
    nickname = Column(String(255))
    photo_url = Column(String(500), nullable=True)  # URL local de la foto de perfil

    # Nivel/Permisos
    level_id = Column(
        Integer, ForeignKey("user_levels.id"), default=6, index=True
    )  # 6 = Free por defecto
    role = Column(String(50), default="user")  # admin, mod, user

    # Flags y Estado
    beta_tester = Column(Boolean, default=False)
    has_library_access = Column(Boolean, default=True)
    can_request_books = Column(Boolean, default=True)
    can_upload_epub = Column(Boolean, default=False)

    # Métricas
    total_downloads = Column(Integer, default=0)

    # JSON Data (Insignias, Metadata extra)
    insignias = Column(JSON, default=list)
    settings = Column(JSON, default=dict)  # Settings JSON blob (Legacy/Fallback)

    # Relaciones UI (Settings estructurados)
    ui_settings = relationship(
        "UserUISettings",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # Relaciones Nivel
    level_info = relationship("UserLevel", back_populates="users")

    # Relaciones Descargas/Votos
    downloads = relationship(
        "UserDownload",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserDownload.user_id",
    )
    ratings = relationship(
        "UserRating",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserRating.user_id",
    )
    uploads = relationship(
        "UploadBook",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UploadBook.telegram_id",
    )

    # Fechas
    expires_at = Column(DateTime, nullable=True)  # Para suscripciones
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "name": self.name,
            "nickname": self.nickname,
            "photo_url": self.photo_url,
            "level": {
                "id": self.level_id,
                "name": self.level_info.name if self.level_info else "free",
                "color": self.level_info.color if self.level_info else "#888888",
            },
            "role": self.role,
            "insignias": self.insignias,
            "total_downloads": self.total_downloads,
            "settings": self.settings,
            "has_library_access": self.has_library_access,
            "can_request_books": self.can_request_books,
            "can_upload_epub": self.can_upload_epub,
        }


class UserLevel(Base):
    """
    Niveles de usuario (Free, Premium, VIP, etc).
    Tabla: user_levels
    """

    __tablename__ = "user_levels"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # python_free, python_premium
    priority = Column(Integer, default=0)

    # Metadata visual
    color = Column(String(20), default="#607D8B")  # Color identificador (badges)

    # UI Defaults del nivel
    ui_theme = Column(String(20), default="dark")
    ui_primary_color = Column(String(20), default="#3b82f6")
    ui_font_size = Column(Integer, default=14)
    ui_nav_opacity = Column(Integer, default=80)
    ui_glass_blur = Column(Integer, default=12)
    ui_cover_width = Column(Integer, default=120)
    ui_accent_opacity = Column(Integer, default=20)
    panel_transparency = Column(Integer, default=60)
    background_color = Column(String(20), default="#0f172a")
    card_color = Column(String(20), default="#1e293b")
    banner_content_offset = Column(Integer, default=0)
    border_radius = Column(Integer, default=24)
    border_width = Column(Integer, default=1)
    force_settings = Column(Boolean, default=False)

    # Características / Pricing
    price = Column(Float, default=0.0)

    # Permisos del nivel
    can_download = Column(Boolean, default=True)
    can_read = Column(Boolean, default=True)
    daily_downloads = Column(Integer, default=5)
    has_mini_app_access = Column(Boolean, default=True)
    has_library_access = Column(Boolean, default=True)
    can_request_books = Column(Boolean, default=True)
    can_upload_epub = Column(Boolean, default=False)
    early_access = Column(Boolean, default=False)
    custom_themes = Column(Boolean, default=False)
    allow_theme_templates = Column(Boolean, default=False)
    show_recommendations = Column(Boolean, default=True)

    # Default Theme Association
    default_theme_id = Column(Integer, ForeignKey("app_themes.id"), nullable=True, index=True)
    default_theme = relationship("AppTheme")

    users = relationship("User", back_populates="level_info")


class UserUISettings(Base):
    """
    Configuración de UI específica del usuario (Overrides).
    Tabla: user_ui_settings (Espejo de Supabase)
    """

    __tablename__ = "user_ui_settings"

    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), primary_key=True)

    theme_type = Column(String(20))
    primary_color = Column(String(20))
    font_size = Column(Integer)
    glass_opacity = Column(Integer)
    nav_opacity = Column(Integer)
    accent_opacity = Column(Integer)
    card_glow_intensity = Column(Integer)
    glass_blur = Column(Integer)
    border_radius = Column(Integer)
    border_width = Column(Integer)
    show_recommendations = Column(Boolean)
    title_language = Column(String(20), default="romaji")

    user = relationship("User", back_populates="ui_settings")


class AppTheme(Base):
    """
    Temas globales de la aplicación (Presets).
    Tabla: app_themes
    """

    __tablename__ = "app_themes"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(500))

    # Visual Properties
    theme_type = Column(String(20), default="dark")  # 'theme' in frontend
    primary_color = Column(String(20))
    background_color = Column(String(20))
    card_color = Column(String(20))

    # Opacities & Effects
    glass_opacity = Column(Integer)
    nav_opacity = Column(Integer)
    accent_opacity = Column(Integer)
    glass_blur = Column(Integer)
    card_glow_intensity = Column(Integer)
    border_radius = Column(Integer, default=24)
    border_width = Column(Integer, default=1)

    # Layout
    font_size = Column(Integer)
    cover_width = Column(Integer)
    banner_content_offset = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
