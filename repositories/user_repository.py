"""
ZeePub Bot: User Repository (V4)
Gestiona las operaciones de base de datos para usuarios, roles y acceso.
Optimizado para PostgreSQL con soporte para patrones V4.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import String, delete, or_, select, update
from sqlalchemy.orm import selectinload

from core.supabase_manager import supabase_manager
from models.user_models import User, UserLevel
from repositories.base_repository import BaseRepository
from repositories.level_repository import LevelRepository, level_repo
from services.cache_service import cache_manager

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """
    Repositorio para gestión de usuarios (roles, expiración, status).
    Implementa el patrón Singleton compatible con servicios V3 y V4.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(User, session=session, db_manager=db_manager)
        self.supabase = supabase_manager
        self.table_name = "users"

    def _to_dict(self, user: User) -> dict[str, Any]:
        """
        Convierte modelo SQLAlchemy User a dict compatible con el frontend.
        """
        # Mapeo de datos básicos
        data = user.to_dict()

        # Enriquecer con info de nivel si está cargado
        level_name = "free"
        level_color = "#888888"
        daily_limit = 5

        if user.level_info:
            level_name = user.level_info.name
            level_color = user.level_info.color or "#888888"
            daily_limit = user.level_info.daily_downloads

        # Recuperar settings de UI (JSONB en V4)
        settings = user.ui_settings or {}

        # Compatibilidad con campos extendidos
        data.update(
            {
                "id": str(user.telegram_id),
                "display_name": user.nickname or user.name or user.username or f"User_{user.telegram_id}",
                "level": {
                    "name": level_name,
                    "color": level_color,
                },
                "level_name": level_name,
                "downloads": {
                    "used": 0,  # Calculado externamente por state_manager o services
                    "limit": daily_limit,
                    "total": user.total_downloads if hasattr(user, "total_downloads") else 0,
                },
                "total_downloads": user.total_downloads if hasattr(user, "total_downloads") else 0,
                "settings": settings,
                "roles": user.roles or [],
                "photo_url": getattr(user, "photo_url", None),
                "email": getattr(user, "email", None),
                "expires_at": getattr(user, "expires_at", None),
                "has_library_access": getattr(user, "has_library_access", True),
                "can_request_books": getattr(user, "can_request_books", True),
                "can_upload_epub": getattr(user, "can_upload_epub", False),
                "allow_theme_templates": getattr(user, "allow_theme_templates", False),
                "beta_tester": getattr(user, "beta_tester", False),
                "bypass_limits": getattr(user, "bypass_limits", False),
            }
        )

        return data

    async def get_by_id(self, telegram_id: int) -> User | None:
        """Obtiene un usuario por su ID de Telegram cargando relaciones."""
        async with self._get_session() as session:
            stmt = select(User).options(selectinload(User.level_info)).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    # Alias para compatibilidad con UserService V4
    get_by_telegram_id = get_by_id

    async def get_by_email(self, email: str) -> User | None:
        """Busca un usuario por su correo electrónico."""
        async with self._get_session() as session:
            stmt = select(User).options(selectinload(User.level_info)).where(User.email == email.lower())
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def upsert(
        self,
        telegram_id: int,
        level: str = "free",
        expires_at: datetime | None = None,
        role: str | None = None,
        nickname: str | None = None,
        name: str | None = None,
        username: str | None = None,
        level_id: int | None = None,
        sync_to_supabase: bool = False,
        **kwargs,
    ) -> User:
        """Inserta o actualiza un usuario."""
        # Mapeo básico de niveles si no se provee level_id
        level_map = {"admin": 1, "staff": 2, "premium": 3, "vip": 4, "white": 5, "free": 6}
        final_level_id = level_id or level_map.get(level.lower(), 6)

        async with self._get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()

            if not user:
                user = User(telegram_id=telegram_id)
                session.add(user)

            # Actualizar campos
            user.level_id = final_level_id
            if expires_at:
                user.expires_at = expires_at
            if role:
                user.role = role
            if nickname:
                user.nickname = nickname
            if name:
                user.name = name
            if username:
                user.username = username

            # Procesar kwargs adicionales (compatibilidad con campos V3)
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            if self.injected_session is None:
                await session.commit()
                await session.refresh(user)

            await cache_manager.invalidate_user(telegram_id)

            # Sync to Supabase if requested
            if sync_to_supabase and self.supabase.is_active:
                try:
                    self.supabase.get_client().table(self.table_name).upsert(user.to_dict()).execute()
                except Exception as e:
                    logger.warning(f"Supabase sync failed for user {telegram_id}: {e}")

            return user

    async def delete(self, telegram_id: int) -> bool:
        """Elimina un usuario por ID."""
        async with self._get_session() as session:
            stmt = delete(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            if self.injected_session is None:
                await session.commit()
            await cache_manager.invalidate_user(telegram_id)
            return result.rowcount > 0

    async def update_status(self, telegram_id: int, new_role: str | None) -> bool:
        """Actualiza el rol funcional del usuario."""
        async with self._get_session() as session:
            stmt = update(User).where(User.telegram_id == telegram_id).values(role=new_role)
            await session.execute(stmt)
            if self.injected_session is None:
                await session.commit()
            await cache_manager.invalidate_user(telegram_id)
            return True

    async def update_nickname(self, telegram_id: int, new_nickname: str | None) -> bool:
        """Actualiza el nickname del usuario."""
        async with self._get_session() as session:
            stmt = update(User).where(User.telegram_id == telegram_id).values(nickname=new_nickname)
            await session.execute(stmt)
            if self.injected_session is None:
                await session.commit()
            await cache_manager.invalidate_user(telegram_id)
            return True

    async def update_user_level(self, telegram_id: int, level_ref: str | int, days: int = 30) -> bool:
        """Actualiza el nivel y expiración de un usuario."""
        async with self._get_session() as session:
            # Buscar nivel
            if isinstance(level_ref, int) or (isinstance(level_ref, str) and level_ref.isdigit()):
                stmt_lvl = select(UserLevel).where(UserLevel.id == int(level_ref))
            else:
                stmt_lvl = select(UserLevel).where(UserLevel.name.ilike(level_ref))

            res_lvl = await session.execute(stmt_lvl)
            level_obj = res_lvl.scalar_one_or_none()

            if not level_obj:
                return False

            # Actualizar usuario
            expires = datetime.now() + timedelta(days=days)
            stmt_user = (
                update(User).where(User.telegram_id == telegram_id).values(level_id=level_obj.id, expires_at=expires)
            )
            await session.execute(stmt_user)
            if self.injected_session is None:
                await session.commit()
            await cache_manager.invalidate_user(telegram_id)
            return True

    async def get_all_levels(self) -> list[dict[str, Any]]:
        """Proxy para level_repo.get_all_as_dict()."""
        return await level_repo.get_all_as_dict()

    async def get_level_by_id(self, level_id: int) -> dict[str, Any] | None:
        """Proxy para level_repo.get_by_id_as_dict()."""
        return await level_repo.get_by_id_as_dict(level_id)

    async def update_level(self, level_id: int, data: dict[str, Any]) -> bool:
        """Proxy para level_repo.update_fields()."""
        return await level_repo.update_fields(level_id, data)

    async def create_minimal_user(self, telegram_id: int, name: str | None = None, username: str | None = None) -> User:
        """Crea un registro básico de usuario."""
        return await self.upsert(telegram_id=telegram_id, name=name, username=username, level="free")

    async def update_telegram_profile(self, telegram_id: int, name: str | None, username: str | None) -> bool:
        """Actualiza datos de perfil de Telegram."""
        async with self._get_session() as session:
            stmt = update(User).where(User.telegram_id == telegram_id).values(name=name, username=username)
            await session.execute(stmt)
            if self.injected_session is None:
                await session.commit()
            await cache_manager.invalidate_user(telegram_id)
            return True

    async def get_access_info(self, telegram_id: int) -> dict[str, Any] | None:
        """Obtiene información detallada de acceso y nivel."""
        user = await self.get_by_id(telegram_id)
        if not user:
            return None

        lvl = user.level_info
        level_dict = {
            "id": str(lvl.id) if lvl else "6",
            "name": lvl.name if lvl else "free",
            "priority": lvl.priority if lvl else 0,
            "color": lvl.color if lvl else "#888888",
            "hasAccess": getattr(lvl, "has_mini_app_access", True) if lvl else True,
            "dailyDownloads": lvl.daily_downloads if lvl else 5,
            "canDownload": lvl.can_download if lvl else True,
            "canRead": getattr(lvl, "can_read", True) if lvl else True,
            "earlyAccess": getattr(lvl, "early_access", False) if lvl else False,
            "customThemes": getattr(lvl, "custom_themes", False) if lvl else False,
            "price": getattr(lvl, "price", 0) if lvl else 0,
            "allowThemeTemplates": getattr(lvl, "allow_theme_templates", False) if lvl else False,
            "theme": getattr(lvl, "ui_theme", "dark") if lvl else "dark",
            "primaryColor": getattr(lvl, "ui_primary_color", "#3b82f6") if lvl else "#3b82f6",
            "fontSize": (getattr(lvl, "ui_font_size", 14) or 14) if lvl else 14,
            "glassBlur": (getattr(lvl, "ui_glass_blur", 12) or 12) if lvl else 12,
            "navOpacity": ((getattr(lvl, "ui_nav_opacity", 80) or 80) / 100.0) if lvl else 0.8,
            "accentOpacity": ((getattr(lvl, "ui_accent_opacity", 20) or 20) / 100.0) if lvl else 0.2,
            "glassOpacity": ((getattr(lvl, "panel_transparency", 60) or 60) / 100.0) if lvl else 0.6,
            "backgroundColor": getattr(lvl, "background_color", "#0f172a") if lvl else "#0f172a",
            "cardColor": getattr(lvl, "card_color", "#1e293b") if lvl else "#1e293b",
            "forceSettings": getattr(lvl, "force_settings", False) if lvl else False,
            "hasLibraryAccess": getattr(lvl, "has_library_access", True) if lvl else True,
            "canRequestBooks": getattr(lvl, "can_request_books", True) if lvl else True,
            "canUploadEpub": getattr(lvl, "can_upload_epub", False) if lvl else False,
        }

        # Roles y banderas
        is_admin = user.role == "admin" or user.level_id == 1

        return {
            "level": level_dict,
            "hasAccess": level_dict["hasAccess"] or is_admin,
            "isAdmin": is_admin,
            "isRealAdmin": is_admin,
            "isBetaTester": getattr(user, "beta_tester", False) or is_admin,
            "name": user.nickname or user.name or f"User_{user.telegram_id}",
            "username": user.username or f"User_{user.telegram_id}",
            "roles": user.roles or [],
            "insignias": getattr(user, "insignias", []),
            "allowThemeTemplates": getattr(user, "allow_theme_templates", False),
            "hasLibraryAccess": getattr(user, "has_library_access", True),
            "canRequestBooks": getattr(user, "can_request_books", True),
            "canUploadEpub": getattr(user, "can_upload_epub", False),
            "photo_url": getattr(user, "photo_url", None),
        }

    async def increment_download_count(self, telegram_id: int) -> int:
        """Incrementa el contador total de descargas."""
        async with self._get_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                user.total_downloads = (getattr(user, "total_downloads", 0) or 0) + 1
                count = user.total_downloads
                if self.injected_session is None:
                    await session.commit()
                await cache_manager.invalidate_user(telegram_id)
                return count
            return 0

    async def update_user_settings(self, telegram_id: int, settings: dict[str, Any]) -> bool:
        """Actualiza la configuración de UI (JSONB)."""
        async with self._get_session() as session:
            stmt = update(User).where(User.telegram_id == telegram_id).values(ui_settings=settings)
            await session.execute(stmt)
            if self.injected_session is None:
                await session.commit()
            await cache_manager.invalidate_user(telegram_id)
            return True

    async def list_users(self, limit: int = 20, offset: int = 0, search: str | None = None) -> list[dict[str, Any]]:
        """
        Lista usuarios paginados con búsqueda opcional.
        Soporta búsqueda por nickname, name, username, email o telegram_id.
        """
        async with self._get_session() as session:
            stmt = select(User).options(selectinload(User.level_info))
            if search:
                search_term = f"%{search}%"
                stmt = stmt.where(
                    or_(
                        User.nickname.ilike(search_term),
                        User.name.ilike(search_term),
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                        User.telegram_id.cast(String).ilike(search_term) if hasattr(User, "telegram_id") else False,
                    )
                )

            stmt = stmt.order_by(User.created_at.desc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return [self._to_dict(u) for u in users]

    async def get_by_level(self, level_name: str) -> list[dict[str, Any]]:
        """Obtiene usuarios por nivel."""
        async with self._get_session() as session:
            # Buscar ID del nivel
            stmt_lvl = select(UserLevel).where(UserLevel.name.ilike(level_name))
            res_lvl = await session.execute(stmt_lvl)
            lvl = res_lvl.scalar_one_or_none()

            if not lvl:
                return []

            stmt_users = select(User).options(selectinload(User.level_info)).where(User.level_id == lvl.id)
            res_users = await session.execute(stmt_users)
            users = res_users.scalars().all()
            return [self._to_dict(u) for u in users]


# Instancia singleton para compatibilidad
user_repo = UserRepository()
UserLevelRepository = LevelRepository  # V3/V4 Compatibility Alias
