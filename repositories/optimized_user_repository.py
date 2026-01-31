import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.user_models import User
from repositories.base_repository import BaseRepository
from services.cache_service import cache_manager

logger = logging.getLogger(__name__)


class OptimizedUserRepository(BaseRepository[dict[str, Any]]):
    """
    Repositorio optimizado para gestión de usuarios con PostgreSQL y Cache-First.
    SQLite eliminado.
    """

    def __init__(self, db=None):
        self.table_name = "users"
        self.supabase = supabase_manager

    async def get_by_id(self, telegram_id: int) -> dict[str, Any] | None:
        # 1. Cache-First
        cached_user = await cache_manager.get_user(telegram_id)
        if cached_user:
            return cached_user

        # 2. Postgres ORM
        try:
            async with pg_manager.get_session() as session:
                stmt = (
                    select(User)
                    .options(selectinload(User.ui_settings), selectinload(User.level_info))
                    .where(User.telegram_id == telegram_id)
                )

                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    settings = user.settings or {}
                    if user.ui_settings:
                        ui = user.ui_settings
                        mapping = {
                            "primary_color": "primaryColor",
                            "glass_blur": "glassBlur",
                            "glass_opacity": "glassOpacity",
                            "nav_opacity": "navOpacity",
                            "accent_opacity": "accentOpacity",
                            "card_glow_intensity": "cardGlowIntensity",
                            "background_color": "backgroundColor",
                            "card_color": "cardColor",
                            "font_size": "fontSize",
                            "cover_width": "coverWidth",
                            "theme_type": "theme",
                        }
                        for col, key in mapping.items():
                            val = getattr(ui, col, None)
                            if val is not None:
                                settings[key] = val

                    user_data = {
                        "telegram_id": user.telegram_id,
                        "level": user.level_id,
                        "expires_at": user.expires_at,
                        "role": user.role,
                        "nickname": user.nickname,
                        "name": user.name or user.nickname,
                        "username": user.username,
                        "roles": [],
                        "insignias": user.insignias or [],
                        "settings": settings,
                        "total_downloads": user.total_downloads or 0,
                        "level_id": user.level_id,
                        "beta_tester": user.beta_tester,
                        "has_library_access": user.has_library_access,
                        "can_request_books": user.can_request_books,
                        "can_upload_epub": user.can_upload_epub,
                        "photo_url": user.photo_url,
                    }
                    await cache_manager.set_user(telegram_id, user_data, 300)
                    return user_data
        except Exception as e:
            logger.error(f"Postgres ORM Error in get_by_id: {e}")

        # 3. Supabase REST Fallback
        if self.supabase.is_active:
            # Similar logic to UserRepo...
            pass

        return None

    async def update_user_level(self, telegram_id: int, level_id: int, level_key: str):
        await cache_manager.invalidate_user(telegram_id)

        # Postgres
        try:
            async with pg_manager.get_session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    user.level_id = level_id
                    if level_key == "admin":
                        user.role = "admin"
                    await session.commit()
        except Exception as e:
            logger.error(f"Postgres update_user_level error: {e}")

        # Supabase
        if self.supabase.is_active:
            try:
                self.supabase.get_client().table("users").update(
                    {"level_id": level_id, "level": level_key}
                ).eq("telegram_id", telegram_id).execute()
            except Exception:
                pass

    async def increment_download_count(self, telegram_id: int):
        await cache_manager.invalidate_user(telegram_id)
        try:
            async with pg_manager.get_session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    user.total_downloads = (user.total_downloads or 0) + 1
                    await session.commit()
        except Exception as e:
            logger.error(f"Postgres increment_download_count error: {e}")

    async def create(self, entity: dict[str, Any]) -> dict[str, Any]:
        return await self.upsert(entity)

    async def update(self, entity: dict[str, Any]) -> dict[str, Any]:
        return await self.upsert(entity)

    async def delete(self, id: int) -> bool:
        await cache_manager.invalidate_user(id)
        try:
            async with pg_manager.get_session() as session:
                stmt = select(User).where(User.telegram_id == id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    await session.delete(user)
                    await session.commit()
                    return True
            return False
        except Exception:
            return False

    async def upsert(self, data: dict[str, Any]) -> dict[str, Any] | None:
        telegram_id = data.get("telegram_id")
        if not telegram_id:
            return None
        await cache_manager.invalidate_user(telegram_id)

        try:
            async with pg_manager.get_session() as session:
                stmt = (
                    pg_insert(User)
                    .values(**data)
                    .on_conflict_do_update(index_elements=["telegram_id"], set_=data)
                    .returning(User)
                )
                await session.execute(stmt)
                await session.commit()
                # ... same mapping as get_by_id ...
                return data
        except Exception as e:
            logger.error(f"Postgres upsert error: {e}")
        return None


optimized_user_repo = OptimizedUserRepository()
