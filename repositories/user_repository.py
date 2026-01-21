from typing import Optional, Dict, Any
from repositories.base_repository import BaseRepository
from core.db_manager import DatabaseManager, db_manager
import logging
from datetime import datetime
from dateutil import parser

from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)

# Cache for level info (5 minutes)
level_cache = AsyncTTLCache(ttl_seconds=300)

from core.db_manager_pg import pg_manager
from models.user_models import User, UserLevel, UserUISettings
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from config.config_settings import config

class UserRepository(BaseRepository[Dict[str, Any]]):
    """
    Repositorio para gestión de usuarios (roles, expiración, status).
    Implementa BaseRepository y añade métodos específicos como upsert.
    """

    def __init__(self, db: DatabaseManager = db_manager):
        self.db = db
        from core.supabase_manager import supabase_manager
        self.supabase = supabase_manager

    async def get_by_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        # 1. Postgres / Offline-First (ORM)
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
                        
                        return {
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
                            "photo_url": user.photo_url
                        }
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
                            # Map relational columns back to settings keys
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
                                if ui_fields.get(col) is not None:
                                    settings[key] = ui_fields[col]
                    except Exception as e:
                        logger.warning(f"Error fetching user_ui_settings: {e}")

                    # Map Supabase result to expected format
                    return {
                        "telegram_id": int(user['telegram_id']),
                        "level": user.get('level', 'free'),
                        "expires_at": self._parse_datetime(user['expires_at']),
                        "role": user.get('role'),
                        "nickname": user['nickname'],
                        "name": user.get('name'),
                        "username": user.get('username'),
                        "roles": [], # Roles column removed
                        "insignias": user.get('insignias') or [],
                        "settings": settings,
                        "total_downloads": user['total_downloads'] or 0,
                        "level_id": user.get('level_id', 6),
                        "photo_url": user.get('photo_url')
                    }
                return None
            except Exception as e:
                logger.error(f"Supabase error in get_by_id: {e}")
                # Fallback to SQLite if needed, or just return None

        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT level, expires_at, role, nickname, settings, total_downloads, name, username, level_id, insignias, photo_url FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            if row:
                level, expires_at_raw, role, nickname, settings_raw, total_downloads, name, username, level_id, insignias_raw, photo_url = row
                expires_at = self._parse_datetime(expires_at_raw)
                import json
                try:
                    settings = json.loads(settings_raw) if settings_raw else {}
                except Exception:
                    settings = {}

                try:
                    insignias = json.loads(insignias_raw) if insignias_raw else []
                except Exception:
                    insignias = []

                return {
                    "telegram_id": telegram_id,
                    "level": level,
                    "expires_at": expires_at,
                    "role": role,
                    "nickname": nickname,
                    "name": name,
                    "username": username,
                    "settings": settings,
                    "total_downloads": total_downloads or 0,
                    "level_id": level_id,
                    "insignias": insignias,
                    "photo_url": photo_url
                }
            return None

    # Métodos de la interfaz base (algunos pueden no usarse directamente si usamos upsert)
    async def create(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        return await self.upsert(
            entity["telegram_id"],
            entity["role"],
            entity.get("expires_at"),
            entity.get("custom_status"),
            entity.get("created_by"),
        )

    async def update(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        return await self.create(entity)

    async def delete(self, telegram_id: int) -> bool:
        async with self.db.connection() as conn:
            await conn.execute(
                "DELETE FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            await conn.commit()
            return True

    # Métodos específicos
    async def upsert(
        self,
        telegram_id: int,
        level: str,
        expires_at: Optional[datetime] = None,
        role: Optional[str] = None,
        created_by: Optional[int] = None,
        nickname: Optional[str] = None,
        name: Optional[str] = None,
        username: Optional[str] = None,
        roles: Optional[list] = None,
        insignias: Optional[list] = None,
        level_id: Optional[int] = None,
        has_library_access: Optional[bool] = None,
        can_request_books: Optional[bool] = None,
        photo_url: Optional[str] = None,
    ):
        # Admin level mapping
        level_to_tier_id = {
            'admin': 1, 'staff': 2, 'premium': 3, 'vip': 4, 'white': 5, 'free': 6, 'user': 6
        }
        level_id = level_id if level_id is not None else level_to_tier_id.get(level.lower(), 6)

        if self.supabase.is_active:
            try:
                import json
                data = {
                    "telegram_id": telegram_id,
                    "level": level.lower(),
                    "level_id": level_id
                }
                if expires_at: data["expires_at"] = expires_at.isoformat()
                if role is not None: data["role"] = role
                if created_by: data["created_by"] = created_by
                if nickname is not None: data["nickname"] = nickname
                if name is not None: data["name"] = name
                if username is not None: data["username"] = username
                # roles column removed from Supabase
                if insignias is not None: data["insignias"] = json.dumps(insignias)
                if has_library_access is not None: data["has_library_access"] = has_library_access
                if can_request_books is not None: data["can_request_books"] = can_request_books
                if photo_url is not None: data["photo_url"] = photo_url
                
                logger.debug(f"[SUPABASE UPSERT] Data: {data}")
                self.supabase.get_client().table('users').upsert(data).execute()
                
                if level.lower() == 'admin':
                    self.supabase.get_client().table('admins').upsert({"user_id": telegram_id, "granted_by": created_by}).execute()
                else:
                    self.supabase.get_client().table('admins').delete().eq('user_id', telegram_id).execute()
            except Exception as e:
                logger.error(f"Supabase upsert error: {e}")

        # 2. Postgres / Offline-First (ORM)
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    # Fetch or create user
                    stmt = select(User).where(User.telegram_id == telegram_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    
                    if not user:
                        user = User(telegram_id=telegram_id)
                        session.add(user)
                    
                    user.level_id = level_id
                    if expires_at is not None: user.expires_at = expires_at
                    if role is not None: user.role = role
                    if nickname is not None: user.nickname = nickname
                    if name is not None: user.name = name
                    if username is not None: user.username = username
                    if insignias is not None: user.insignias = insignias
                    if has_library_access is not None: user.has_library_access = has_library_access
                    if can_request_books is not None: user.can_request_books = can_request_books
                    if photo_url is not None: user.photo_url = photo_url
                    
                    await session.commit()
                    logger.info(f"[POSTGRES UPSERT] Success for user {telegram_id}")
            except Exception as e:
                logger.error(f"Postgres ORM error in upsert: {e}")

        # 3. SQLite Fallback (Optional, but kept for legacy)

        async with self.db.connection() as conn:
            # Check existence
            cursor = await conn.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            exists = await cursor.fetchone()

            if exists:
                import json
                fields = ["level = ?", "level_id = ?"]
                params = [level, level_id]
                if expires_at is not None:
                    fields.append("expires_at = ?")
                    params.append(expires_at)
                if role is not None:
                    fields.append("role = ?")
                    params.append(role)
                if created_by is not None:
                    fields.append("created_by = ?")
                    params.append(created_by)
                if nickname is not None:
                    fields.append("nickname = ?")
                    params.append(nickname)
                if name is not None:
                    fields.append("name = ?")
                    params.append(name)
                if username is not None:
                    fields.append("username = ?")
                    params.append(username)
                if roles is not None:
                    fields.append("roles = ?")
                    params.append(json.dumps(roles))
                if insignias is not None:
                    fields.append("insignias = ?")
                    params.append(json.dumps(insignias))
                if has_library_access is not None:
                    fields.append("has_library_access = ?")
                    params.append(1 if has_library_access else 0)
                if can_request_books is not None:
                    fields.append("can_request_books = ?")
                    params.append(1 if can_request_books else 0)
                if photo_url is not None:
                    fields.append("photo_url = ?")
                    params.append(photo_url)

                params.append(telegram_id)
                sql = f"UPDATE users SET {', '.join(fields)} WHERE telegram_id = ?"
                await conn.execute(sql, tuple(params))
            else:
                import json
                await conn.execute(
                    "INSERT INTO users (telegram_id, level, level_id, added_at, expires_at, role, created_by, nickname, name, username, roles, insignias, has_library_access, can_request_books, settings, photo_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?)",
                    (
                        telegram_id,
                        level,
                        level_id,
                        datetime.utcnow(),
                        expires_at,
                        role,
                        created_by,
                        nickname,
                        name,
                        username,
                        json.dumps(roles) if roles is not None else '[]',
                        json.dumps(insignias) if insignias is not None else '[]',
                        int(has_library_access if has_library_access is not None else True),
                        int(can_request_books if can_request_books is not None else True),
                        photo_url
                    ),
                )

            # Sync with admins table
            if level.lower() == 'admin':
                await conn.execute(
                    "INSERT OR IGNORE INTO admins (user_id, granted_by) VALUES (?, ?)",
                    (telegram_id, created_by)
                )
            elif exists:
                await conn.execute("DELETE FROM admins WHERE user_id = ?", (telegram_id,))

            await conn.commit()
            return {"telegram_id": telegram_id, "level": level}

    async def update_status(self, telegram_id: int, role: Optional[str]):
        if self.supabase.is_active:
            try:
                self.supabase.get_client().table('users').update({"role": role}).eq('telegram_id', telegram_id).execute()
            except Exception as e:
                logger.error(f"Supabase status error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET role = ? WHERE telegram_id = ?",
                (role, telegram_id),
            )
            await conn.commit()

    async def get_by_level(self, level: str) -> list[Dict[str, Any]]:
        results = []
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT telegram_id, level, expires_at FROM users WHERE level = ?",
                (level,),
            )
            rows = await cursor.fetchall()
            for row in rows:
                telegram_id, lvl, expires_raw = row
                results.append(
                    {
                        "telegram_id": telegram_id,
                        "level": lvl,
                        "expires_at": self._parse_datetime(expires_raw),
                    }
                )
        return results

    async def update_nickname(self, telegram_id: int, nickname: Optional[str]):
        if self.supabase.is_active:
            try:
                self.supabase.get_client().table('users').update({"nickname": nickname}).eq('telegram_id', telegram_id).execute()
            except Exception as e:
                logger.error(f"Supabase update_nickname error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET nickname = ? WHERE telegram_id = ?",
                (nickname, telegram_id),
            )
            await conn.commit()

    async def get_access_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        # 0. Check Cache for user access info
        # We don't cache access info here because it's already cached in user_service.py

        # 1. Postgres / Offline-First (ORM)
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                # Same eagerness as get_by_id
                async with pg_manager.get_session() as session:
                    stmt = select(User).options(
                        selectinload(User.ui_settings),
                        selectinload(User.level_info)
                    ).where(User.telegram_id == telegram_id)
                    
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if user:
                        lvl = user.level_info
                        # Map Level
                        # Basic logic: If no level, assume free
                        # This mapping MUST match the dict returned by Supabase/SQLite for frontend/bot consistency
                        level_dict = {
                            "id": str(lvl.id) if lvl else "6",
                            "name": lvl.name if lvl else "python_free",
                            "priority": lvl.priority if lvl else 0,
                            "color": lvl.color if lvl else "#3b82f6",
                            "hasAccess": lvl.has_mini_app_access if lvl else True,
                            "dailyDownloads": lvl.daily_downloads if lvl else 5,
                            "canDownload": lvl.can_download if lvl else True,
                            "canRead": lvl.can_read if lvl else True,
                            "earlyAccess": lvl.early_access if lvl else False,
                            "customThemes": lvl.custom_themes if lvl else False,
                            "price": lvl.price if lvl else 0,
                            "showRecommendations": lvl.show_recommendations if lvl else True,
                            
                            # UI Tokens
                            "theme": lvl.ui_theme if lvl else "dark",
                            "primaryColor": lvl.ui_primary_color if lvl else "#3b82f6",
                            "fontSize": lvl.ui_font_size if lvl else 14,
                            "glassBlur": lvl.ui_glass_blur if lvl else 12,
                            "coverWidth": lvl.ui_cover_width if lvl else 120,
                            "navOpacity": lvl.ui_nav_opacity if lvl else 0.8,
                            "accentOpacity": lvl.ui_accent_opacity if lvl else 0.2,
                            "glassOpacity": (lvl.panel_transparency or 60) / 100.0 if lvl else 0.6,
                            "backgroundColor": lvl.background_color if lvl else "#0f172a",
                            "cardColor": lvl.card_color if lvl else "#1e293b",
                            "forceSettings": lvl.force_settings if lvl else False,
                            "bannerContentOffset": lvl.banner_content_offset if lvl else 0,
                            "hasLibraryAccess": lvl.has_library_access if lvl else True,
                            "canRequestBooks": lvl.can_request_books if lvl else True
                        }
                        
                        # Apply User UI Settings Overrides
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
                                    if key in ["glassOpacity", "navOpacity", "accentOpacity"] and float(val) > 1:
                                        level_dict[key] = float(val) / 100.0
                                    else:
                                        level_dict[key] = val

                        # Admin Check
                        is_admin = (user.role == 'admin') or (user.telegram_id in config.ADMIN_USERS)
                        beta_tester = user.beta_tester or is_admin

                        return {
                            "level": level_dict,
                            "hasAccess": level_dict["hasAccess"] or is_admin,
                            "isAdmin": is_admin,
                            "isBetaTester": beta_tester,
                            "name": user.name or user.nickname, # UI Fallback
                            "username": user.username,
                            "roles": [],
                            "insignias": user.insignias or [],
                            "hasLibraryAccess": user.has_library_access,
                            "canRequestBooks": user.can_request_books,
                            "photo_url": user.photo_url
                        }
            except Exception as e:
                logger.error(f"Postgres ORM Error in get_access_info: {e}")
                # Fallthrough to Supabase REST / SQLite

        if self.supabase.is_active:
            try:
                # Use explicit column list instead of * to avoid error with defunct 'roles' column
                cols = "telegram_id, level, expires_at, role, nickname, name, username, insignias, settings, total_downloads, level_id, beta_tester, has_library_access, can_request_books, photo_url"
                res = self.supabase.get_client().table('users').select(f"{cols}, level:user_levels(*)").eq('telegram_id', telegram_id).execute()
                if res.data:
                    user = res.data[0]
                    lvl = user.get('level_info', user.get('level', {})) # Join name is 'level' but column is also 'level'
                    # Wait, Supabase join usually uses the name of the join. 
                    # If the column is named 'level', and join is named 'level', there might be a conflict.
                    # But the execution shows 'level' column has 'free'.
                    
                    is_admin = (user.get('level') == 'admin')
                    beta_tester = user.get('beta_tester', False) or is_admin  # Admins are always beta testers
                    # check admins table too if needed, but role='admin' is usually enough
                    return {
                        "level": {
                            "id": str(lvl.get('id')),
                            "name": lvl.get('name'),
                            "priority": lvl.get('priority'),
                            "color": lvl.get('color'),
                            "hasAccess": bool(lvl.get('has_mini_app_access')),
                            "dailyDownloads": lvl.get('daily_downloads'),
                            "earlyAccess": bool(lvl.get('early_access')),
                            "customThemes": bool(lvl.get('custom_themes')),
                            "price": lvl.get('price'),
                            "showRecommendations": bool(lvl.get('show_recommendations', True)),
                            "theme": lvl.get('ui_theme', 'dark'),
                            "fontSize": lvl.get('ui_font_size', 14),
                            "glassBlur": lvl.get('ui_glass_blur', 12),
                            "coverWidth": lvl.get('ui_cover_width', 120),
                            "navOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(lvl.get('ui_nav_opacity', 0.8)),
                            "accentOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(lvl.get('ui_accent_opacity', 0.2)),
                            "glassOpacity": (lvl.get('panel_transparency', 60) or 60) / 100.0,
                            "primaryColor": lvl.get('ui_primary_color', '#2b6cee'),
                            "canDownload": bool(lvl.get('can_download', True)),
                            "canRead": bool(lvl.get('can_read', True)),
                            "hasLibraryAccess": bool(lvl.get('has_library_access', True)),
                            "canRequestBooks": bool(lvl.get('can_request_books', True)),
                            "bannerContentOffset": int(lvl.get('banner_content_offset', 0)),
                            "backgroundColor": lvl.get('background_color', '#0f172a'),
                            "cardColor": lvl.get('card_color', '#1e293b'),
                            "forceSettings": bool(lvl.get('force_settings', False)),
                        },
                        "hasAccess": bool(lvl.get('has_mini_app_access')) or is_admin,
                        "isAdmin": is_admin,
                        "isBetaTester": beta_tester,
                        "name": user.get('name'),
                        "username": user.get('username'),
                        "roles": [], # Roles column removed
                        "insignias": user.get('insignias') or [],
                        "hasLibraryAccess": bool(user.get('has_library_access', True)),
                        "canRequestBooks": bool(user.get('can_request_books', True)),
                        "photo_url": user.get('photo_url')
                    }
            except Exception as e:
                logger.error(f"Supabase access info error: {e}")

        query = """
            SELECT
                ul.id,
                ul.name,
                ul.priority,
                ul.color,
                ul.has_mini_app_access,
                ul.daily_downloads,
                ul.early_access,
                ul.custom_themes,
                ul.price,
                ul.show_recommendations,
                (EXISTS(SELECT 1 FROM admins WHERE user_id = ?) OR u.level = 'admin') as is_admin,
                u.level,
                u.settings,
                ul.ui_theme,
                ul.ui_font_size,
                ul.ui_glass_blur,
                ul.ui_cover_width,
                ul.ui_nav_opacity,
                ul.ui_accent_opacity,
                ul.panel_transparency,
                ul.ui_primary_color,
                u.name,
                u.username,
                u.nickname,
                u.insignias,
                u.has_library_access,
                u.can_request_books,
                ul.can_download,
                ul.can_read,
                ul.has_library_access as ul_has_library_access,
                ul.can_request_books as ul_can_request_books,
                ul.banner_content_offset,
                ul.background_color,
                ul.card_color,
                ul.force_settings,
                u.photo_url
            FROM users u
            INNER JOIN user_levels ul ON u.level_id = ul.id
            WHERE u.telegram_id = ?
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(query, (telegram_id, telegram_id))
            row = await cursor.fetchone()
            if row:
                is_admin = bool(row[10])
                level = row[11] if len(row) > 11 else 'free'
                
                # Parse settings
                settings = {}
                try:
                    import json
                    settings_str = row[12] if len(row) > 12 else "{}"
                    if settings_str:
                        settings = json.loads(settings_str)
                except Exception:
                    pass

                # For SQLite, treat admin and staff as beta testers 
                beta_tester = is_admin or level in ('admin', 'staff')
                
                import json
                return {
                    "level": {
                        "id": str(row[0]),
                        "name": row[1],
                        "priority": row[2],
                        "color": row[3],
                        "hasAccess": bool(row[4]),
                        "dailyDownloads": row[5],
                        "earlyAccess": bool(row[6]),
                        "customThemes": bool(row[7]),
                        "price": row[8],
                        "showRecommendations": bool(row[9]) if len(row) > 9 else True,
                        "theme": row[13] if len(row) > 13 else 'dark',
                        "fontSize": row[14] if len(row) > 14 else 14,
                        "glassBlur": row[15] if len(row) > 15 else 12,
                        "coverWidth": row[16] if len(row) > 16 else 120,
                        "navOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(row[17] if len(row) > 17 else 0.8),
                        "accentOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(row[18] if len(row) > 18 else 0.2),
                        "glassOpacity": (row[19] if len(row) > 19 else 60) / 100.0,
                        "primaryColor": row[20] if len(row) > 20 else '#2b6cee',
                        "canDownload": bool(row[27]) if len(row) > 27 else True,
                        "canRead": bool(row[28]) if len(row) > 28 else True,
                        "hasLibraryAccess": bool(row[29]) if len(row) > 29 else True,
                        "canRequestBooks": bool(row[30]) if len(row) > 30 else True,
                        "bannerContentOffset": int(row[31]) if len(row) > 31 else 0,
                        "backgroundColor": row[32] if len(row) > 32 else '#0f172a',
                        "cardColor": row[33] if len(row) > 33 else '#1e293b',
                        "forceSettings": bool(row[34]) if len(row) > 34 else False,
                    },
                    "hasAccess": bool(row[4]) or is_admin,  # Access if level allowed OR if admin
                    "isAdmin": is_admin,
                    "isBetaTester": beta_tester,
                    "name": row[21] if len(row) > 21 else None,
                    "username": row[22] if len(row) > 22 else None,
                    "roles": [], # Roles column removed
                    "nickname": row[23] if len(row) > 23 else None,
                    "insignias": json.loads(row[24]) if len(row) > 24 and row[24] else [],
                    "hasLibraryAccess": bool(row[25]) if len(row) > 25 else True,
                    "canRequestBooks": bool(row[26]) if len(row) > 26 else True,
                    "photo_url": row[35] if len(row) > 35 else None
                }
            return None

    async def create_minimal_user(self, telegram_id: int, level_id: int = 6, nickname: Optional[str] = None):
        """
        Crea un registro básico de usuario si no existe.
        Level 6 = Lector (default), role = 'free'
        """
        if self.supabase.is_active:
            try:
                # Check if exists first
                res = self.supabase.get_client().table('users').select('telegram_id').eq('telegram_id', telegram_id).execute()
                if not res.data:
                    self.supabase.get_client().table('users').insert({
                        "telegram_id": telegram_id,
                        "level_id": level_id,
                        "level": 'free',
                        "nickname": nickname
                    }).execute()
            except Exception as e:
                logger.error(f"Supabase create_minimal_user error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, level_id, level, added_at, nickname) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, level_id, 'free', datetime.utcnow(), nickname)
            )
            await conn.commit()

    async def get_level_by_id(self, level_id: int) -> Optional[Dict[str, Any]]:
        """Busca la configuración de un nivel por su ID."""
        # 0. Check Cache First
        cache_key = f"level_info:{level_id}"
        cached = await level_cache.get(cache_key)
        if cached:
            return cached
            
        # Also check if it's already in the all_levels cache
        all_lvls = await level_cache.get("all_levels")
        if all_lvls:
            match = next((l for l in all_lvls if l['id'] == str(level_id)), None)
            if match:
                await level_cache.set(cache_key, match)
                return match

        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_levels').select("*").eq('id', level_id).execute()
                if res.data:
                    lvl = res.data[0]
                    result = {
                        "id": str(lvl.get('id')),
                        "name": lvl.get('name'),
                        "priority": lvl.get('priority'),
                        "color": lvl.get('color'),
                        "hasAccess": bool(lvl.get('has_mini_app_access')),
                        "dailyDownloads": lvl.get('daily_downloads'),
                        "earlyAccess": bool(lvl.get('early_access')),
                        "customThemes": bool(lvl.get('custom_themes')),
                        "price": lvl.get('price'),
                        "showRecommendations": bool(lvl.get('show_recommendations', True)),
                        "theme": lvl.get('ui_theme', 'dark'),
                        "fontSize": lvl.get('ui_font_size', 14),
                        "glassBlur": lvl.get('ui_glass_blur', 12),
                        "coverWidth": lvl.get('ui_cover_width', 120),
                        "navOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(lvl.get('ui_nav_opacity', 0.8)),
                        "accentOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(lvl.get('ui_accent_opacity', 0.2)),
                        "glassOpacity": (lvl.get('panel_transparency', 60) or 60) / 100.0,
                        "primaryColor": lvl.get('ui_primary_color', '#2b6cee'),
                        "cardGlowIntensity": lvl.get('ui_glow_intensity', 0.5),
                        "canDownload": bool(lvl.get('can_download', True)),

                        "canRead": bool(lvl.get('can_read', True)),
                        "hasLibraryAccess": bool(lvl.get('has_library_access', True)),
                        "canRequestBooks": bool(lvl.get('can_request_books', True)),
                        "bannerContentOffset": int(lvl.get('banner_content_offset', 0)),
                        "backgroundColor": lvl.get('background_color', '#0f172a'),
                        "cardColor": lvl.get('card_color', '#1e293b'),
                        "forceSettings": bool(lvl.get('force_settings', False)),
                    }
                    await level_cache.set(cache_key, result)
                    return result
                return None
            except Exception as e:
                logger.error(f"Supabase error in get_level_by_id: {e}")

        async with self.db.connection() as conn:
            # Explicit column selection to avoid index issues
            query = """
                SELECT 
                    id, name, priority, color, has_mini_app_access, daily_downloads, early_access, 
                    custom_themes, price, show_recommendations, ui_theme, ui_font_size, ui_glass_blur, 
                    ui_cover_width, ui_nav_opacity, ui_accent_opacity, panel_transparency, 
                    "ui_primary_color", "can_download", "can_read", "has_library_access", "can_request_books", 
                    "banner_content_offset", "background_color", "card_color", "force_settings", "ui_glow_intensity"
                FROM user_levels WHERE id = ?
            """
            cursor = await conn.execute(query, (level_id,))
            r = await cursor.fetchone()
            if r:
                result = {
                    "id": str(r[0]),
                    "name": r[1],
                    "priority": r[2],
                    "color": r[3],
                    "hasAccess": bool(r[4]),
                    "dailyDownloads": r[5],
                    "earlyAccess": bool(r[6]),
                    "customThemes": bool(r[7]),
                    "price": r[8],
                    "showRecommendations": bool(r[9]),
                    "theme": r[10] or 'dark',
                    "fontSize": r[11] or 14,
                    "glassBlur": r[12] or 12,
                    "coverWidth": r[13] or 120,
                    "navOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(r[14] or 0.8),
                    "accentOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(r[15] or 0.2),
                    "glassOpacity": (r[16] or 60) / 100.0,
                    "primaryColor": r[17] or '#2b6cee',
                    "canDownload": bool(r[18]) if r[18] is not None else True,
                    "canRead": bool(r[19]) if r[19] is not None else True,
                    "hasLibraryAccess": bool(r[20]) if r[20] is not None else True,
                    "canRequestBooks": bool(r[21]) if r[21] is not None else True,
                    "bannerContentOffset": int(r[22]) if r[22] is not None else 0,
                    "backgroundColor": r[23] or '#0f172a',
                    "cardColor": r[24] or '#1e293b',
                    "forceSettings": bool(r[25]) if r[25] is not None else False,
                    "cardGlowIntensity": r[26] if len(r) > 26 else 0.5,
                }
                await level_cache.set(cache_key, result)
                return result

        return None

    async def get_all_levels(self) -> list[Dict[str, Any]]:
        """
        Retorna todos los niveles configurados con sus límites y características.
        """
        # Check Cache
        cached = await level_cache.get("all_levels")
        if cached:
            return cached

        results = []
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_levels').select("*").order('priority', desc=True).execute()
                if res.data:
                    results = [
                        {
                            "id": str(row['id']),
                            "name": row['name'],
                            "priority": row['priority'],
                            "color": row['color'],
                            "hasAccess": bool(row['has_mini_app_access']),
                            "dailyDownloads": row['daily_downloads'],
                            "earlyAccess": bool(row['early_access']),
                            "customThemes": bool(row['custom_themes']),
                            "price": row['price'],
                            "showRecommendations": bool(row.get('show_recommendations', True)),
                            "theme": row.get('ui_theme', 'dark'),
                            "fontSize": row.get('ui_font_size', 14),
                            "glassBlur": row.get('ui_glass_blur', 12),
                            "coverWidth": row.get('ui_cover_width', 120),
                            "navOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(row.get('ui_nav_opacity', 0.8)),
                            "accentOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(row.get('ui_accent_opacity', 0.2)),
                            "glassOpacity": (row.get('panel_transparency', 60) or 60) / 100.0,
                            "primaryColor": row.get('ui_primary_color', '#2b6cee'),
                            "cardGlowIntensity": row.get('ui_glow_intensity', 0.5),
                            "canDownload": bool(row.get('can_download', True)),
                            "canRead": bool(row.get('can_read', True)),
                            "hasLibraryAccess": bool(row.get('has_library_access', True)),
                            "canRequestBooks": bool(row.get('can_request_books', True)),
                            "bannerContentOffset": int(row.get('banner_content_offset', 0)),
                            "backgroundColor": row.get('background_color', '#0f172a'),
                            "cardColor": row.get('card_color', '#1e293b'),
                            "forceSettings": bool(row.get('force_settings', False)),
                        }
                        for row in res.data
                    ]
                    await level_cache.set("all_levels", results)
                    return results
            except Exception as e:
                logger.error(f"Supabase get_all_levels error: {e}")

        # SQLite/Postgres Fallback
        query = "SELECT id, name, priority, color, has_mini_app_access, daily_downloads, early_access, custom_themes, price, show_recommendations, ui_theme, ui_font_size, ui_glass_blur, ui_cover_width, ui_nav_opacity, ui_accent_opacity, panel_transparency, ui_primary_color, has_library_access, can_request_books, ui_glow_intensity, can_download, can_read, banner_content_offset, background_color, card_color, force_settings FROM user_levels ORDER BY priority DESC"
        async with self.db.connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            results = [
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "priority": row[2],
                    "color": row[3],
                    "hasAccess": bool(row[4]),
                    "dailyDownloads": row[5],
                    "earlyAccess": bool(row[6]),
                    "customThemes": bool(row[7]),
                    "price": row[8],
                    "showRecommendations": bool(row[9]),
                    "theme": row[10] or 'dark',
                    "fontSize": row[11] or 14,
                    "glassBlur": row[12] or 12,
                    "coverWidth": row[13] or 120,
                    "navOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(row[14] or 0.8),
                    "accentOpacity": (lambda x: float(x)/100.0 if x is not None and float(x) > 1 else x)(row[15] or 0.2),
                    "glassOpacity": (row[16] or 60) / 100.0,
                    "primaryColor": row[17] or '#2b6cee',
                    "cardGlowIntensity": row[20] if len(row) > 19 else 0.5,
                    "canDownload": bool(row[21]) if len(row) > 20 else True,
                    "canRead": bool(row[22]) if len(row) > 21 else True,
                    "bannerContentOffset": int(row[23]) if len(row) > 22 else 0,
                    "backgroundColor": row[24] if len(row) > 23 else '#0f172a',
                    "cardColor": row[25] if len(row) > 24 else '#1e293b',
                    "forceSettings": bool(row[26]) if len(row) > 25 else False,
                }
                for row in rows
            ]
            await level_cache.set("all_levels", results)
            return results

    async def list_users(self, limit: int = 50, offset: int = 0, search: str = None) -> list[Dict[str, Any]]:
        # 1. Postgres / Offline-First (ORM)
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    stmt = select(User).options(selectinload(User.level_info)).order_by(User.updated_at.desc())
                    
                    if search:
                        # Simple case-insensitive search
                        stmt = stmt.where(
                            (User.nickname.ilike(f"%{search}%")) | 
                            (User.username.ilike(f"%{search}%")) |
                            (User.name.ilike(f"%{search}%")) |
                            (cast(User.telegram_id, String).ilike(f"%{search}%"))
                        )
                    
                    stmt = stmt.limit(limit).offset(offset)
                    result = await session.execute(stmt)
                    users = result.scalars().all()
                    
                    results = []
                    for user in users:
                        lvl = user.level_info
                        level_dict = {
                            "name": lvl.name if lvl else "N-A",
                            "color": getattr(lvl, 'color', '#888888')
                        }
                        
                        results.append({
                            "id": str(user.telegram_id),
                            "username": user.nickname or f"User_{user.telegram_id}",
                            "name": user.name,
                            "telegram_username": user.username,
                            "photo_url": user.photo_url,
                            "level_name": lvl.name if lvl else "free",
                            "level": level_dict,
                            "role": user.role,
                            "downloads": {
                                "used": 0, # TODO: Query actual daily usage
                                "limit": lvl.daily_downloads if lvl else 5,
                                "total": user.total_downloads
                            }
                        })
                    return results

            except Exception as e:
                logger.error(f"Postgres ORM Error in list_users: {e}")
                # Fallthrough

        if self.supabase.is_active:
            try:
                cols = "telegram_id, nickname, name, username, level_id, role, total_downloads, updated_at, photo_url"
                query = self.supabase.get_client().table('users').select(f"{cols}, level:user_levels(name, color, daily_downloads)")
                if search:
                    # Supabase doesn't support easy OR complex filters via wrapper as nicely, but we can try
                    query = query.or_(f"nickname.ilike.%{search}%,telegram_id.eq.{search}")
                
                res = query.order('updated_at', desc=True).range(offset, offset + limit - 1).execute()
                
                results = []
                for user in res.data:
                    lvl = user.get('level', {})
                    results.append({
                        "id": str(user['telegram_id']),
                        "username": user['nickname'] or f"User_{user['telegram_id']}",
                        "name": user.get('name'),
                        "telegram_username": user.get('username'),
                        "photo_url": user.get('photo_url'),
                        "level_name": user.get('level_id'), # String/ID level
                        "level": { # Rename from level_info to level to match AdminUser interface
                            "name": lvl.get('name') or "N-A",
                            "color": lvl.get('color') or "#888888"
                        },
                        "role": user.get('role'),
                        "downloads": {
                            "used": 0, # Placeholder
                            "limit": lvl.get('daily_downloads') or 5,
                            "total": user['total_downloads'] or 0
                        }
                    })
                return results
            except Exception as e:
                logger.error(f"Supabase list_users error: {e}")

        """
        Retorna la lista de usuarios con su nivel y estadísticas de descargas.
        """
        query = """
            SELECT 
                u.telegram_id, 
                u.nickname, 
                u.level, 
                ul.name as level_name, 
                ul.color as level_color,
                u.total_downloads,
                ul.daily_downloads,
                u.name,
                u.username,
                u.role,
                u.photo_url
            FROM users u
            LEFT JOIN user_levels ul ON u.level_id = ul.id
        """
        params = []
        if search:
            query += " WHERE u.nickname LIKE ? OR CAST(u.telegram_id AS TEXT) LIKE ?"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY u.added_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = []
        async with self.db.connection() as conn:
            cursor = await conn.execute(query, tuple(params))
            rows = await cursor.fetchall()
            for row in rows:
                tid, nickname, tier, l_name, l_color, total_dl, daily_limit = row[:7]
                role = row[9] if len(row) > 9 else None
                
                # Fetch downloads today from state_manager proxy if possible or just return a placeholder
                # In a real app we'd query download_history for today
                used_today = 0 # Placeholder, should be fetched per-user in a real scenario
                
                results.append({
                    "id": str(tid),
                    "username": nickname or f"User_{tid}",
                    "name": row[7] if len(row) > 7 else None,
                    "telegram_username": row[8] if len(row) > 8 else None,
                    "photo_url": row[10] if len(row) > 10 else None,
                    "level_name": tier,
                    "level": { # Rename from level_info to level
                        "name": l_name or "N-A",
                        "color": l_color or "#888888"
                    },
                    "downloads": {
                        "used": used_today,
                        "limit": daily_limit,
                        "total": total_dl
                    }
                })
        return results

    async def update_user_level(self, telegram_id: int, level_id: int):
        """Cambia el nivel de un usuario."""
        # Mapping level_id to role for consistency
        level_to_role = {
            1: 'admin',
            2: 'staff',
            3: 'premium',
            4: 'vip',
            5: 'white',
            6: 'free'
        }
        level_key = level_to_role.get(level_id, 'free')
        
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

    async def update_level(self, level_id: int, data: Dict[str, Any]):
        """
        Actualiza la configuración de un nivel.
        """
        fields = []
        params = []
        sb_data = {}
        
        mapping = {
            "hasAccess": "has_mini_app_access",
            "dailyDownloads": "daily_downloads",
            "earlyAccess": "early_access",
            "customThemes": "custom_themes",
            "showRecommendations": "show_recommendations",
            "price": "price",
            "name": "name",
            "color": "color",
            "theme": "ui_theme",
            "fontSize": "ui_font_size",
            "glassBlur": "ui_glass_blur",
            "coverWidth": "ui_cover_width",
            "navOpacity": "ui_nav_opacity",
            "accentOpacity": "ui_accent_opacity",
            "glassOpacity": "panel_transparency",
            "primaryColor": "ui_primary_color",
            "cardGlowIntensity": "ui_glow_intensity",
            "canDownload": "can_download",
            "canRead": "can_read",
            "backgroundColor": "background_color",
            "cardColor": "card_color",
            "forceSettings": "force_settings",
            "bannerContentOffset": "banner_content_offset",
            "hasLibraryAccess": "has_library_access",
            "canRequestBooks": "can_request_books",
        }

        
        for key, col in mapping.items():
            if key in data:
                fields.append(f"{col} = ?")
                val = data[key]
                if isinstance(val, bool):
                    val = 1 if val else 0
                params.append(val)
                sb_data[col] = data[key]
        
        if not fields:
            return

        if self.supabase.is_active and sb_data:
            try:
                self.supabase.get_client().table('user_levels').update(sb_data).eq('id', level_id).execute()
            except Exception as e:
                logger.error(f"Supabase update_level error: {e}")
        
        # Postgres Plugin
        if config.ENABLE_POSTGRES_PLUGIN and sb_data:
            try:
                async with pg_manager.get_session() as session:
                    stmt = select(UserLevel).where(UserLevel.id == level_id)
                    result = await session.execute(stmt)
                    lvl = result.scalar_one_or_none()
                    if lvl:
                        for col, val in sb_data.items():
                            if hasattr(lvl, col):
                                setattr(lvl, col, val)
                        await session.commit()
            except Exception as e:
                logger.error(f"Postgres update_level error: {e}")
            
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(level_id)
        
        query = f"UPDATE user_levels SET {', '.join(fields)} WHERE id = ?"
        async with self.db.connection() as conn:
            await conn.execute(query, tuple(params))
            await conn.commit()

    async def is_admin(self, telegram_id: int) -> bool:
        """
        Verifica si un usuario está en la tabla de admins.
        """
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('admins').select("user_id").eq('user_id', telegram_id).execute()
                if res.data:
                    return True
            except Exception as e:
                logger.error(f"Supabase is_admin error: {e}")

        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT 1 FROM admins WHERE user_id = ?", (telegram_id,)
            )
            return await cursor.fetchone() is not None

    async def get_user_by_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Alias de get_by_id para consistencia."""
        return await self.get_by_id(telegram_id)

    async def update_user_settings(self, telegram_id: int, settings: Dict[str, Any]):
        """Actualiza el campo JSON settings de un usuario."""
        import json
        settings_json = json.dumps(settings)
        
        if self.supabase.is_active:
            try:
                # 1. Update main user record (JSON blob)
                self.supabase.get_client().table('users').update({
                    "settings": settings
                }).eq('telegram_id', telegram_id).execute()

                # 2. Update relational UI settings (columns)
                mapping = {
                    "primaryColor": "primary_color",
                    "glassBlur": "glass_blur",
                    "glassOpacity": "glass_opacity",
                    "navOpacity": "nav_opacity",
                    "accentOpacity": "accent_opacity",
                    "cardGlowIntensity": "card_glow_intensity",
                    "backgroundColor": "background_color",
                    "cardColor": "card_color",
                    "fontSize": "font_size",
                    "coverWidth": "cover_width",
                    "theme": "theme_type"
                }
                
                ui_data = {"user_id": str(telegram_id), "updated_at": "now()"}
                for key, col in mapping.items():
                    if key in settings:
                        ui_data[col] = settings[key]
                
                if len(ui_data) > 2: # More than just user_id and updated_at
                    self.supabase.get_client().table('user_ui_settings').upsert(ui_data, on_conflict='user_id').execute()

            except Exception as e:
                logger.error(f"Supabase update settings error: {e}")

        # Postgres Plugin
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    # 1. Update User.settings (JSON)
                    stmt = select(User).where(User.telegram_id == telegram_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    if user:
                        user.settings = settings
                        
                        # 2. Update UserUISettings (Relation)
                        mapping = {
                            "primaryColor": "primary_color",
                            "glassBlur": "glass_blur",
                            "glassOpacity": "glass_opacity",
                            "navOpacity": "nav_opacity",
                            "accentOpacity": "accent_opacity",
                            "cardGlowIntensity": "card_glow_intensity",
                            "backgroundColor": "background_color",
                            "cardColor": "card_color",
                            "fontSize": "font_size",
                            "coverWidth": "cover_width",
                            "theme": "theme_type"
                        }
                        
                        stmt_ui = select(UserUISettings).where(UserUISettings.user_id == telegram_id)
                        res_ui = await session.execute(stmt_ui)
                        ui = res_ui.scalar_one_or_none()
                        
                        if not ui:
                            ui = UserUISettings(user_id=telegram_id)
                            session.add(ui)
                        
                        for key, col in mapping.items():
                            if key in settings:
                                val = settings[key]
                                if key in ["glassOpacity", "navOpacity", "accentOpacity"] and float(val) > 1:
                                    val = float(val) / 100.0
                                setattr(ui, col, val)
                        
                        await session.commit()
            except Exception as e:
                logger.error(f"Postgres update_user_settings error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET settings = ? WHERE telegram_id = ?",
                (settings_json, telegram_id),
            )
            await conn.commit()

    async def increment_download_count(self, telegram_id: int) -> int:
        if self.supabase.is_active:
            try:
                # Direct increment is harder via REST without RPC, but we can do a read-modify-write or RPC
                # RPC is better: create function increment_total_downloads(uid bigint)
                # But for now, read-modify-write if we don't have the RPC setup
                res = self.supabase.get_client().table('users').select('total_downloads').eq('telegram_id', telegram_id).execute()
                if res.data:
                    new_count = (res.data[0]['total_downloads'] or 0) + 1
                    self.supabase.get_client().table('users').update({"total_downloads": new_count}).eq('telegram_id', telegram_id).execute()
                    return new_count
            except Exception as e:
                logger.error(f"Supabase increment error: {e}")

        """Incrementa el contador total de descargas de un usuario y retorna el nuevo valor."""
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET total_downloads = total_downloads + 1 WHERE telegram_id = ?",
                (telegram_id,),
            )
            cursor = await conn.execute(
                "SELECT total_downloads FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            await conn.commit()
            return row[0] if row else 0

    def _parse_datetime(self, val: Any) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            try:
                return parser.parse(val)
            except Exception:
                return None
        return None

    async def reset_level_users_settings(self, level_id: int):
        """
        Resetea (borra) la configuración personal de todos los usuarios de un nivel.
        Establece 'settings' a '{}'.
        """
        if self.supabase.is_active:
            try:
                # 1. Get user IDs of this level
                res = self.supabase.get_client().table('users').select('telegram_id').eq('level_id', level_id).execute()
                uids = [str(r['telegram_id']) for r in res.data]
                if uids:
                    # 2. Reset main settings
                    self.supabase.get_client().table('users').update({"settings": {}}).eq('level_id', level_id).execute()
                    # 3. Delete from relational settings
                    self.supabase.get_client().table('user_ui_settings').delete().in_('user_id', uids).execute()
            except Exception as e:
                logger.error(f"Supabase reset error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET settings = '{}' WHERE level_id = ?",
                (level_id,),
            )
            await conn.commit()
    
    async def create_minimal_user(self, telegram_id: int, name: Optional[str] = None, username: Optional[str] = None):
        """Crea un registro básico para un nuevo usuario."""
        return await self.upsert(
            telegram_id=telegram_id,
            level='free',
            name=name,
            username=username
        )

# Singleton instance
user_repo = UserRepository()
