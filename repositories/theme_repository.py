from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository
from core.db_manager import DatabaseManager, db_manager
from models.user_models import AppTheme
from config.config_settings import config
from core.db_manager_pg import pg_manager
from sqlalchemy import select, delete
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ThemeRepository(BaseRepository[Dict[str, Any]]):
    """
    Repositorio para gestión de temas (AppTheme).
    Soporta Postgres/SQLite/Offline.
    """

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db

    async def ensure_default_themes(self):
        """Si no hay temas en la DB, crea unos por defecto."""
        try:
            # Use PostgreSQL if enabled, otherwise SQLite
            # PostgreSQL is the base
            async with pg_manager.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT count(*) FROM app_themes"))
                count = result.scalar()
                if count > 0:
                    return

            logger.info("Seeding default theme templates...")
            defaults = [
                {
                    "name": "Ocean Deep (Default)",
                    "description": "El balance perfecto entre legibilidad y estética profesional.",
                    "theme": "dark",
                    "primaryColor": "#2b6cee",
                    "backgroundColor": "#0f172a",
                    "cardColor": "#1e293b",
                    "glassOpacity": 0.6,
                    "glassBlur": 12,
                    "cardGlowIntensity": 0.5,
                    "fontSize": 14,
                    "coverWidth": 120,
                    "bannerContentOffset": 0
                },
                {
                    "name": "Midnight Purple",
                    "description": "Elegancia nocturna con tonos violetas y burdeos.",
                    "theme": "dark",
                    "primaryColor": "#a855f7",
                    "backgroundColor": "#1a1a2e",
                    "cardColor": "#16213e",
                    "glassOpacity": 0.7,
                    "glassBlur": 16,
                    "cardGlowIntensity": 0.6,
                    "fontSize": 14,
                    "coverWidth": 120,
                    "bannerContentOffset": 0
                },
                {
                    "name": "Emerald Night",
                    "description": "Inspirado en bosques profundos y terminales antiguas.",
                    "theme": "dark",
                    "primaryColor": "#10b981",
                    "backgroundColor": "#064e3b",
                    "cardColor": "#065f46",
                    "glassOpacity": 0.5,
                    "glassBlur": 10,
                    "cardGlowIntensity": 0.4,
                    "fontSize": 14,
                    "coverWidth": 120,
                    "bannerContentOffset": 0
                },
                {
                    "name": "Amoled Black",
                    "description": "Contraste máximo para pantallas OLED. Ahorro de batería y pureza visual.",
                    "theme": "dark",
                    "primaryColor": "#3b82f6",
                    "backgroundColor": "#000000",
                    "cardColor": "#111111",
                    "glassOpacity": 0.4,
                    "glassBlur": 8,
                    "cardGlowIntensity": 0.3,
                    "fontSize": 14,
                    "coverWidth": 120,
                    "bannerContentOffset": 0
                }
            ]
            
            for theme in defaults:
                await self.upsert(theme)
            
        except Exception as e:
            logger.error(f"Error seeding default themes: {e}")

    async def get_all_themes(self) -> List[Dict[str, Any]]:
        # Asegurar que existan temas por defecto antes de listar
        await self.ensure_default_themes()

        # Use local PostgreSQL
        # Use PostgreSQL exclusively
        try:
            async with pg_manager.get_session() as session:
                stmt = select(AppTheme).order_by(AppTheme.name)
                result = await session.execute(stmt)
                themes = result.scalars().all()
                theme_list = [self._to_dict(t) for t in themes]
                logger.info(f"Retrieved {len(theme_list)} themes from PostgreSQL")
                return theme_list
        except Exception as e:
            logger.error(f"Postgres get_all_themes error: {e}")
            return []

    async def upsert(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        name = data.get("name")
        if not name: return None
        
        # Mapping
        theme_data = {
            "name": name,
            "description": data.get("description"),
            "theme_type": data.get("theme_type") or data.get("theme"),
            "primary_color": data.get("primary_color") or data.get("primaryColor"),
            "background_color": data.get("background_color") or data.get("backgroundColor"),
            "card_color": data.get("card_color") or data.get("cardColor"),
            "glass_opacity": data.get("glass_opacity") or data.get("glassOpacity"),
            "nav_opacity": data.get("nav_opacity") or data.get("navOpacity"),
            "accent_opacity": data.get("accent_opacity") or data.get("accentOpacity"),
            "glass_blur": data.get("glass_blur") or data.get("glassBlur"),
            "card_glow_intensity": data.get("card_glow_intensity") or data.get("cardGlowIntensity"),
            "font_size": data.get("font_size") or data.get("fontSize"),
            "cover_width": data.get("cover_width") or data.get("coverWidth"),
            "banner_content_offset": data.get("banner_content_offset") or data.get("bannerContentOffset"),
            "updated_at": datetime.utcnow()
        }

        # 1. Postgres
        # Use PostgreSQL exclusively
        try:
            async with pg_manager.get_session() as session:
                stmt = select(AppTheme).where(AppTheme.name == name)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    for k, v in theme_data.items():
                        if v is not None:
                            setattr(existing, k, v)
                else:
                    existing = AppTheme(**theme_data)
                    session.add(existing)
                
                await session.commit()
                return self._to_dict(existing)
        except Exception as e:
            logger.error(f"Postgres upsert theme error: {e}")
            return None

    def _to_dict(self, theme: AppTheme) -> Dict[str, Any]:
        return {
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "theme": theme.theme_type,
            "primaryColor": theme.primary_color,
            "backgroundColor": theme.background_color,
            "cardColor": theme.card_color,
            "glassOpacity": theme.glass_opacity,
            "navOpacity": theme.nav_opacity,
            "accentOpacity": theme.accent_opacity,
            "glassBlur": theme.glass_blur,
            "cardGlowIntensity": theme.card_glow_intensity,
            "fontSize": theme.font_size,
            "coverWidth": theme.cover_width,
            "bannerContentOffset": theme.banner_content_offset
        }

    # Helper for interface
    async def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        return None
    async def create(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        return await self.upsert(entity)
    async def update(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        return await self.upsert(entity)
    async def delete(self, id: int) -> bool:
        return False

theme_repo = ThemeRepository()
