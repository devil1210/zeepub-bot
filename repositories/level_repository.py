"""
ZeePub Bot: Level Repository
Gestiona las operaciones de base de datos para UserLevel.
Extraído de user_repository.py para adherir al principio de responsabilidad única.
"""

import logging
from typing import Any

from sqlalchemy import select, text

from core.db_manager_pg import pg_manager
from models.users import UserLevel
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

# Niveles por defecto del sistema (fuente de verdad)
DEFAULT_LEVELS: list[dict[str, Any]] = [
    {
        "id": "1",
        "name": "Administrador",
        "priority": 100,
        "color": "#FF4B4B",
        "price": 0.0,
        "dailyDownloads": -1,
        "canDownload": True,
        "canRead": True,
        "hasAccess": True,
        "allowThemeTemplates": True,
        "earlyAccess": True,
        "customThemes": True,
        "canUploadEpub": True,
    },
    {
        "id": "2",
        "name": "Staff",
        "priority": 90,
        "color": "#4ECDC4",
        "price": 0.0,
        "dailyDownloads": 50,
        "canDownload": True,
        "canRead": True,
        "hasAccess": True,
        "allowThemeTemplates": True,
        "earlyAccess": True,
        "customThemes": True,
        "canUploadEpub": False,
    },
    {
        "id": "3",
        "name": "Premium",
        "priority": 80,
        "color": "#FFD93D",
        "price": 0.0,
        "dailyDownloads": 50,
        "canDownload": True,
        "canRead": False,
        "hasAccess": True,
        "allowThemeTemplates": True,
        "earlyAccess": False,
        "customThemes": False,
        "canUploadEpub": False,
    },
    {
        "id": "4",
        "name": "VIP",
        "priority": 70,
        "color": "#1A5F7A",
        "price": 0.0,
        "dailyDownloads": 20,
        "canDownload": True,
        "canRead": False,
        "hasAccess": True,
        "allowThemeTemplates": True,
        "earlyAccess": False,
        "customThemes": False,
        "canUploadEpub": False,
    },
    {
        "id": "5",
        "name": "Patrocinador",
        "priority": 60,
        "color": "#FFFFFF",
        "price": 0.0,
        "dailyDownloads": 10,
        "canDownload": True,
        "canRead": False,
        "hasAccess": True,
        "allowThemeTemplates": True,
        "earlyAccess": True,
        "customThemes": False,
        "canUploadEpub": False,
    },
    {
        "id": "6",
        "name": "Gratis",
        "priority": 0,
        "color": "#888888",
        "price": 0.0,
        "dailyDownloads": 2,
        "canDownload": True,
        "canRead": False,
        "hasAccess": True,
        "allowThemeTemplates": True,
        "earlyAccess": False,
        "customThemes": False,
        "canUploadEpub": False,
    },
]

# Mapeo de nombre de nivel a ID
LEVEL_NAME_TO_ID: dict[str, int] = {
    "admin": 1,
    "administrador": 1,
    "staff": 2,
    "premium": 3,
    "vip": 4,
    "white": 5,
    "patrocinador": 5,
    "free": 6,
    "gratis": 6,
}


class LevelRepository(BaseRepository[UserLevel]):
    """Repositorio para gestión de niveles de usuario (UserLevel)."""

    def __init__(self, db_manager=None):
        super().__init__(db_manager or pg_manager, "user_levels")

    async def get_by_id(self, id: Any) -> UserLevel | None:
        """Obtiene un nivel por su ID."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(UserLevel).where(UserLevel.id == id))
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> UserLevel | None:
        """Obtiene un nivel por nombre (case-insensitive)."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(UserLevel).where(UserLevel.name.ilike(name)))
            return result.scalar_one_or_none()

    async def get_by_ref(self, level_ref: str | int) -> UserLevel | None:
        """Obtiene un nivel por ID o nombre."""
        if isinstance(level_ref, int) or (isinstance(level_ref, str) and level_ref.isdigit()):
            return await self.get_by_id(int(level_ref))
        return await self.get_by_name(str(level_ref))

    async def create(self, entity: UserLevel) -> UserLevel:
        async with self.db_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: UserLevel) -> UserLevel:
        async with self.db_manager.get_session() as session:
            await session.merge(entity)
            await session.commit()
            return entity

    async def delete(self, id: Any) -> bool:
        from sqlalchemy import delete as sa_delete

        async with self.db_manager.get_session() as session:
            result = await session.execute(sa_delete(UserLevel).where(UserLevel.id == id))
            await session.commit()
            return result.rowcount > 0

    async def get_all(self) -> list[UserLevel]:
        """Devuelve todos los niveles ordenados por prioridad descendente."""
        async with self.db_manager.get_session() as session:
            result = await session.execute(select(UserLevel).order_by(UserLevel.priority.desc()))
            return list(result.scalars().all())

    async def get_all_as_dict(self) -> list[dict[str, Any]]:
        """Devuelve todos los niveles como dicts listos para la API."""
        try:
            levels = await self.get_all()
            if not levels:
                await self.ensure_defaults()
                levels = await self.get_all()
            if not levels:
                return DEFAULT_LEVELS
            return [self._level_to_dict(lvl) for lvl in levels]
        except Exception as e:
            logger.error(f"[LevelRepository] Error fetching levels: {e}")
            return DEFAULT_LEVELS

    async def get_by_id_as_dict(self, level_id: int) -> dict[str, Any] | None:
        """Obtiene un nivel por ID como dict."""
        try:
            lvl = await self.get_by_id(level_id)
            return self._level_to_dict(lvl) if lvl else None
        except Exception as e:
            logger.error(f"[LevelRepository] Error fetching level {level_id}: {e}")
            return None

    async def update_fields(self, level_id: int, data: dict[str, Any]) -> bool:
        """Actualiza campos específicos de un nivel mediante mapeo frontend→DB."""
        _FIELD_MAP = {
            "name": "name",
            "priority": "priority",
            "color": "color",
            "price": "price",
            "dailyDownloads": "daily_downloads",
            "canDownload": "can_download",
            "canRead": "can_read",
            "hasAccess": "has_mini_app_access",
            "allowThemeTemplates": "allow_theme_templates",
            "earlyAccess": "early_access",
            "customThemes": "custom_themes",
            "showRecommendations": "show_recommendations",
            "defaultThemeId": "default_theme_id",
            "theme": "ui_theme",
            "primaryColor": "ui_primary_color",
            "fontSize": "ui_font_size",
            "glassBlur": "ui_glass_blur",
            "navOpacity": "ui_nav_opacity",
            "accentOpacity": "ui_accent_opacity",
            "backgroundColor": "background_color",
            "cardColor": "card_color",
            "forceSettings": "force_settings",
            "borderRadius": "border_radius",
            "borderWidth": "border_width",
            "canUploadEpub": "can_upload_epub",
            "hasLibraryAccess": "has_library_access",
            "canRequestBooks": "can_request_books",
        }
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(select(UserLevel).where(UserLevel.id == level_id))
                level = result.scalar_one_or_none()
                if not level:
                    logger.warning(f"[LevelRepository] Level {level_id} not found.")
                    return False

                for key, col in _FIELD_MAP.items():
                    if key in data:
                        setattr(level, col, data[key])

                if "glassOpacity" in data:
                    val = data["glassOpacity"]
                    level.panel_transparency = int(val * 100) if isinstance(val, float) and val <= 1.0 else int(val)

                if "bannerContentOffset" in data:
                    level.banner_content_offset = int(data["bannerContentOffset"])

                await session.commit()
                return True
        except Exception as e:
            logger.error(f"[LevelRepository] Error updating level {level_id}: {e}")
            return False

    async def update_access(self, level_id: int, has_access: bool) -> bool:
        """Helper para actualizar solo el flag de acceso."""
        return await self.update_fields(level_id, {"hasAccess": has_access})

    async def ensure_defaults(self) -> None:
        """Seed de niveles por defecto si la tabla está vacía."""
        try:
            async with self.db_manager.get_session() as session:
                count = (await session.execute(text("SELECT count(*) FROM user_levels"))).scalar()
                if count and count > 0:
                    return

                logger.info("[LevelRepository] Seeding default user levels...")
                for lvl in DEFAULT_LEVELS:
                    await session.execute(
                        text("""
                            INSERT INTO user_levels (
                                id, name, priority, color, price, daily_downloads,
                                can_download, can_read, has_mini_app_access,
                                has_library_access, can_request_books, can_upload_epub,
                                early_access, custom_themes, allow_theme_templates, show_recommendations
                            ) VALUES (
                                :id, :name, :priority, :color, :price, :dailyDownloads,
                                :canDownload, :canRead, :hasAccess,
                                :has_library_access, :can_request_books, :canUploadEpub,
                                :earlyAccess, :customThemes, :allowThemeTemplates, :show_recommendations
                            )
                        """),
                        {
                            "id": int(lvl["id"]),
                            "name": lvl["name"],
                            "priority": lvl["priority"],
                            "color": lvl["color"],
                            "price": lvl["price"],
                            "dailyDownloads": lvl["dailyDownloads"],
                            "canDownload": lvl["canDownload"],
                            "canRead": lvl["canRead"],
                            "hasAccess": lvl["hasAccess"],
                            "has_library_access": lvl.get("has_library_access", True),
                            "can_request_books": lvl.get("can_request_books", True),
                            "canUploadEpub": lvl.get("canUploadEpub", False),
                            "earlyAccess": lvl["earlyAccess"],
                            "customThemes": lvl["customThemes"],
                            "allowThemeTemplates": lvl["allowThemeTemplates"],
                            "show_recommendations": lvl.get("show_recommendations", True),
                        },
                    )
                await session.commit()
                logger.info("[LevelRepository] Default levels seeded successfully.")
        except Exception as e:
            logger.error(f"[LevelRepository] Error seeding defaults: {e}")

    def _level_to_dict(self, lvl: UserLevel) -> dict[str, Any]:
        """Convierte un UserLevel a dict compatible con la API frontend."""
        return {
            "id": str(lvl.id),
            "name": lvl.name,
            "priority": lvl.priority,
            "color": lvl.color,
            "price": lvl.price,
            "dailyDownloads": lvl.daily_downloads,
            "canDownload": lvl.can_download,
            "canRead": lvl.can_read,
            "hasAccess": lvl.has_mini_app_access,
            "allowThemeTemplates": lvl.allow_theme_templates,
            "earlyAccess": lvl.early_access,
            "customThemes": lvl.custom_themes,
            "canUploadEpub": getattr(lvl, "can_upload_epub", False),
            "hasLibraryAccess": getattr(lvl, "has_library_access", True),
            "canRequestBooks": getattr(lvl, "can_request_books", True),
        }


level_repo = LevelRepository()
