from typing import Optional, Dict, Any
from repositories.base_repository import BaseRepository
from core.db_manager import DatabaseManager, db_manager
import logging
from datetime import datetime
from dateutil import parser

from services.cache_service import cache_manager
from core.db_manager_pg import pg_manager
from models.user_models import User, UserLevel, UserUISettings
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from config.config_settings import config
from core.supabase_manager import supabase_manager
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

class OptimizedUserRepository(BaseRepository[Dict[str, Any]]):
    """
    Repositorio optimizado para gestión de usuarios con cache-first approach.
    Implementa BaseRepository y añade métodos específicos optimizados.
    """

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db
        from core.supabase_manager import supabase_manager
        self.supabase = supabase_manager

    async def get_by_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        # 1. Cache-First (más rápido)
        cached_user = await cache_manager.get_user(telegram_id)
        if cached_user:
            return cached_user
        
        # 2. Postgres / Offline-First (ORM)
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    # Eager load UI settings and Level
                    stmt = select(User).options(
                        selectinload(User.ui_settings),
                        selectinload(User.level_info)
                    ).where(User.telegram_id == telegram_id)
                    
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    
                    if user:
                        # Map ORM object to dict (similar structure to old one)
                        settings = user.settings or {}
                        
                        # Apply UI Settings overrides from relation
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
                                "theme_type": "theme"
                            }
                            for col, key in mapping.items():
                                val = getattr(ui, col, None)
                                if val is not None:
                                    settings[key] = val

                        level_name = user.level_info.name if user.level_info else "free"
                        
                        user_data = {
                            "telegram_id": user.telegram_id,
                            "level": user.level_id, # Fallback name
                            "expires_at": user.expires_at,
                            "role": user.role,
                            "nickname": user.nickname,
                            "name": user.name or user.nickname, # UI Fallback
                            "username": user.username,
                            "roles": [], # Legacy
                            "insignias": user.insignias or [],
                            "settings": settings,
                            "total_downloads": user.total_downloads or 0,
                            "level_id": user.level_id,
                            "beta_tester": user.beta_tester,
                            "has_library_access": user.has_library_access,
                            "can_request_books": user.can_request_books,
                            "can_upload_epub": user.can_upload_epub,
                            "photo_url": user.photo_url
                        }
                        
                        # Guardar en cache para futuras consultas
                        await cache_manager.set_user(telegram_id, user_data, 300)
                        return user_data
            except Exception as e:
                logger.error(f"Postgres ORM Error in get_by_id: {e}")
                # Fallthrough to Supabase REST / SQLite

        if self.supabase.is_active:
            try:
                cols = "telegram_id, level, expires_at, role, nickname, name, username, insignias, settings, total_downloads, level_id, beta_tester, has_library_access, can_request_books, photo_url"
                res = self.supabase.get_client().table('users').select(cols).eq('telegram_id', telegram_id).execute()
                if res.data:
                    user = res.data[0]
                    settings = user['settings'] or {}
                    
                    # Fetch relational UI settings if they exist
                    try:
                        ui_res = self.supabase.get_client().table('user_ui_settings').select("*").eq('user_id', str(telegram_id)).execute()
                        if ui_res.data:
                            ui_fields = ui_res.data[0]
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
                                "theme_type": "theme"
                            }
                            for col, key in mapping.items():
                                val = ui_fields.get(col)
                                if val is not None:
                                    settings[key] = val
                    except Exception as ui_err:
                        logger.warning(f"Could not fetch UI settings for user {telegram_id}: {ui_err}")
                    
                    user_data = {
                        "telegram_id": user['telegram_id'],
                        "level": user.get('level', 'free'),
                        "expires_at": parser.parse(user['expires_at']) if user.get('expires_at') else None,
                        "role": user.get('role', 'user'),
                        "nickname": user.get('nickname'),
                        "name": user.get('name') or user.get('nickname'),
                        "username": user.get('username'),
                        "roles": [], # Legacy
                        "insignias": user.get('insignias', []),
                        "settings": settings,
                        "total_downloads": user.get('total_downloads', 0),
                        "level_id": user.get('level_id', 6),
                        "beta_tester": user.get('beta_tester', False),
                        "has_library_access": user.get('has_library_access', True),
                        "can_request_books": user.get('can_request_books', True),
                        "can_upload_epub": user.get('can_upload_epub', False),
                        "photo_url": user.get('photo_url')
                    }
                    
                    # Guardar en cache
                    await cache_manager.set_user(telegram_id, user_data, 300)
                    return user_data
            except Exception as e:
                logger.error(f"Supabase REST Error in get_by_id: {e}")

        # 3. SQLite (Fallback)
        try:
            async with self.db.connection() as conn:
                cursor = await conn.execute("""
                    SELECT u.*, us.*, ul.name as level_name, ul.color as level_color 
                    FROM users u 
                    LEFT JOIN user_ui_settings us ON u.telegram_id = us.user_id 
                    LEFT JOIN user_levels ul ON u.level_id = ul.id 
                    WHERE u.telegram_id = ?
                """, (telegram_id,))
                
                row = await cursor.fetchone()
                if row:
                    # Map row to dict (similar to above)
                    settings = {}
                    ui_fields = [col for col in row.keys() if col.startswith('ui_') and row[col] is not None]
                    for col in ui_fields:
                        mapping = {
                            "ui_primary_color": "primaryColor",
                            "ui_glass_blur": "glassBlur",
                            "ui_glass_opacity": "glassOpacity",
                            "ui_nav_opacity": "navOpacity",
                            "ui_accent_opacity": "accentOpacity",
                            "ui_card_glow_intensity": "cardGlowIntensity",
                            "ui_background_color": "backgroundColor",
                            "ui_card_color": "cardColor",
                            "ui_font_size": "fontSize",
                            "ui_cover_width": "coverWidth",
                            "ui_theme_type": "theme"
                        }
                        key = mapping.get(col)
                        if key:
                            settings[key] = row[col]
                    
                    user_data = {
                        "telegram_id": row['telegram_id'],
                        "level": row['level_name'] or 'free',
                        "expires_at": row['expires_at'],
                        "role": row['role'] or 'user',
                        "nickname": row['nickname'],
                        "name": row['name'] or row['nickname'],
                        "username": row['username'],
                        "roles": [], # Legacy
                        "insignias": row['insignias'] or [],
                        "settings": settings,
                        "total_downloads": row['total_downloads'] or 0,
                        "level_id": row['level_id'],
                        "beta_tester": row['beta_tester'] or False,
                        "has_library_access": row['has_library_access'] if row['has_library_access'] is not None else True,
                        "can_request_books": row['can_request_books'] if row['can_request_books'] is not None else True,
                        "can_upload_epub": row['can_upload_epub'] if row['can_upload_epub'] is not None else False,
                        "photo_url": row['photo_url']
                    }
                    
                    # Guardar en cache
                    await cache_manager.set_user(telegram_id, user_data, 300)
                    return user_data
        except Exception as e:
            logger.error(f"SQLite Error in get_by_id: {e}")
        
        return None

    async def update_user_level(self, telegram_id: int, level_id: int, level_key: str):
        """Actualiza el nivel de un usuario en todas las bases de datos."""
        
        # Invalidar cache del usuario
        await cache_manager.invalidate_user(telegram_id)
        
        # Supabase
        if self.supabase.is_active:
            try:
                # Use upsert to create user if doesn't exist
                self.supabase.get_client().table('users').upsert({
                    "telegram_id": telegram_id,
                    "level_id": level_id,
                    "level": level_key
                }, on_conflict="telegram_id").execute()
                
                # Sync admins table in Supabase (only if user now exists)
                if level_key == 'admin':
                    try:
                        self.supabase.get_client().table('admins').upsert({"user_id": telegram_id}).execute()
                    except Exception as admin_err:
                        logger.warning(f"Could not add to admins table: {admin_err}")
                else:
                    self.supabase.get_client().table('admins').delete().eq('user_id', telegram_id).execute()
            except Exception as e:
                logger.error(f"Supabase update_user_level error: {e}")

        # Postgres Plugin
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    stmt = select(User).where(User.telegram_id == telegram_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if user:
                        user.level_id = level_id
                        user.level = level_key
                        if level_key == 'admin': user.role = 'admin'
                        await session.commit()
            except Exception as e:
                logger.error(f"Postgres update_user_level error: {e}")

        # SQLite fallback
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET level_id = ?, level = ? WHERE telegram_id = ?",
                (level_id, level_key, telegram_id)
            )
            # Sync admins table
            if level_key == 'admin':
                await conn.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (telegram_id,))
            else:
                await conn.execute("DELETE FROM admins WHERE user_id = ?", (telegram_id,))
            await conn.commit()

    async def increment_download_count(self, telegram_id: int):
        """Incrementa el contador de descargas de un usuario."""
        
        # Invalidar cache
        await cache_manager.invalidate_user(telegram_id)
        
        # Postgres
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    stmt = select(User).where(User.telegram_id == telegram_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if user:
                        user.total_downloads = (user.total_downloads or 0) + 1
                        await session.commit()
                        return
            except Exception as e:
                logger.error(f"Postgres increment_download_count error: {e}")

        # SQLite fallback
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET total_downloads = total_downloads + 1 WHERE telegram_id = ?",
                (telegram_id,)
            )
            await conn.commit()

    # Implementar otros métodos necesarios para compatibilidad
    async def create(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        return await self.upsert(entity)
    
    async def update(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        return await self.upsert(entity)
    
    async def delete(self, id: int) -> bool:
        # Invalidar cache
        await cache_manager.invalidate_user(id)
        return False
    
    async def upsert(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Implementación optimizada de upsert."""
        telegram_id = data.get('telegram_id')
        if not telegram_id:
            return None
            
        # Invalidar cache
        await cache_manager.invalidate_user(telegram_id)
        
        # Implementar upsert optimizado para PostgreSQL
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    stmt = pg_insert(User).values(**data).on_conflict_do_update(
                        index_elements=['telegram_id'],
                        set_=data
                    ).returning(User)
                    
                    result = await session.execute(stmt)
                    await session.commit()
                    
                    user = result.scalar_one()
                    user_data = {
                        "telegram_id": user.telegram_id,
                        "level": user.level_id,
                        "expires_at": user.expires_at,
                        "role": user.role,
                        "nickname": user.nickname,
                        "name": user.name,
                        "username": user.username,
                        "settings": user.settings,
                        "total_downloads": user.total_downloads,
                        "level_id": user.level_id,
                        "beta_tester": user.beta_tester,
                        "has_library_access": user.has_library_access,
                        "can_request_books": user.can_request_books,
                        "can_upload_epub": user.can_upload_epub,
                        "photo_url": user.photo_url
                    }
                    
                    # Guardar en cache
                    await cache_manager.set_user(telegram_id, user_data, 300)
                    return user_data
            except Exception as e:
                logger.error(f"Postgres upsert error: {e}")
        
        return None

# Instancia global optimizada
optimized_user_repo = OptimizedUserRepository()
