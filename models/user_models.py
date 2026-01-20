from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, BigInteger, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class User(Base):
    """
    Representa un usuario del bot (Telegram).
    Espejo de la tabla 'users' en Supabase.
    """
    __tablename__ = 'users'

    # Telegram ID es la PK (BigInteger para soportar IDs de Telegram)
    telegram_id = Column(BigInteger, primary_key=True, autoincrement=False)
    
    # Perfil
    username = Column(String(255))
    name = Column(String(255))
    nickname = Column(String(255))
    
    # Nivel/Permisos
    level_id = Column(Integer, ForeignKey('user_levels.id'), default=6) # 6 = Free por defecto
    role = Column(String(50), default='user') # admin, mod, user
    
    # Flags y Estado
    beta_tester = Column(Boolean, default=False)
    has_library_access = Column(Boolean, default=True)
    can_request_books = Column(Boolean, default=True)
    
    # Métricas
    total_downloads = Column(Integer, default=0)
    
    # JSON Data (Insignias, Metadata extra)
    insignias = Column(JSON, default=list)
    settings = Column(JSON, default=dict) # Settings JSON blob (Legacy/Fallback)
    
    # Relaciones UI (Settings estructurados)
    ui_settings = relationship("UserUISettings", uselist=False, back_populates="user", cascade="all, delete-orphan")
    
    # Relaciones Nivel
    level_info = relationship("UserLevel", back_populates="users")
    
    # Relaciones Descargas/Votos
    # downloads = relationship("UserDownload", back_populates="user") # Definido en library models
    # ratings = relationship("UserRating", back_populates="user")     # Definido en library models

    # Fechas
    expires_at = Column(DateTime, nullable=True) # Para suscripciones
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "name": self.name,
            "level": self.level_info.name if self.level_info else "free",
            "level_id": self.level_id,
            "role": self.role,
            "insignias": self.insignias,
            "total_downloads": self.total_downloads,
            "settings": self.settings
        }

class UserLevel(Base):
    """
    Niveles de usuario (Free, Premium, VIP, etc).
    Tabla: user_levels
    """
    __tablename__ = 'user_levels'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # python_free, python_premium
    priority = Column(Integer, default=0)
    
    # Metadata visual
    color = Column(String(20), default='#607D8B') # Color identificador (badges)
    
    # UI Defaults del nivel
    ui_theme = Column(String(20), default='dark')
    ui_primary_color = Column(String(20), default='#3b82f6')
    ui_nav_opacity = Column(Integer, default=80)
    ui_glass_blur = Column(Integer, default=12)
    ui_cover_width = Column(Integer, default=120)
    ui_accent_opacity = Column(Integer, default=20)
    panel_transparency = Column(Integer, default=60)
    
    # Características / Pricing
    price = Column(Integer, default=0) # Consider float/Numeric if needed, usually int/cents or simple float
    # Note: price in miniapp_handlers seems to be float/int.
    
    # Permisos del nivel
    can_download = Column(Boolean, default=True)
    daily_downloads = Column(Integer, default=5)
    has_mini_app_access = Column(Boolean, default=True)
    early_access = Column(Boolean, default=False)
    custom_themes = Column(Boolean, default=False)
    
    users = relationship("User", back_populates="level_info")

class UserUISettings(Base):
    """
    Configuración de UI específica del usuario (Overrides).
    Tabla: user_ui_settings (Espejo de Supabase)
    """
    __tablename__ = 'user_ui_settings'
    
    user_id = Column(BigInteger, ForeignKey('users.telegram_id'), primary_key=True)
    
    theme_type = Column(String(20))
    primary_color = Column(String(20))
    glass_opacity = Column(Integer)
    card_glow_intensity = Column(Integer)
    # ... otros campos UI
    
    user = relationship("User", back_populates="ui_settings")
