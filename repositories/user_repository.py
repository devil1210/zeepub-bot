from typing import Optional, Dict, Any
from repositories.base_repository import BaseRepository
from core.db_manager import DatabaseManager, db_manager
import logging
from datetime import datetime
from dateutil import parser

logger = logging.getLogger(__name__)


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
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('users').select("*").eq('telegram_id', telegram_id).execute()
                if res.data:
                    user = res.data[0]
                    # Map Supabase result to expected format
                    return {
                        "telegram_id": int(user['telegram_id']),
                        "role": user['role'],
                        "expires_at": self._parse_datetime(user['expires_at']),
                        "custom_status": user['custom_status'],
                        "nickname": user['nickname'],
                        "settings": user['settings'] or {},
                        "total_downloads": user['total_downloads'] or 0,
                    }
                return None
            except Exception as e:
                logger.error(f"Supabase error in get_by_id: {e}")
                # Fallback to SQLite if needed, or just return None

        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT role, expires_at, custom_status, nickname, settings, total_downloads FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            if row:
                role, expires_at_raw, custom_status, nickname, settings_raw, total_downloads = row
                expires_at = self._parse_datetime(expires_at_raw)
                import json
                try:
                    settings = json.loads(settings_raw) if settings_raw else {}
                except Exception:
                    settings = {}

                return {
                    "telegram_id": telegram_id,
                    "role": role,
                    "expires_at": expires_at,
                    "custom_status": custom_status,
                    "nickname": nickname,
                    "settings": settings,
                    "total_downloads": total_downloads or 0,
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
        role: str,
        expires_at: Optional[datetime] = None,
        custom_status: Optional[str] = None,
        created_by: Optional[int] = None,
        nickname: Optional[str] = None,
    ):
        # Admin level mapping
        role_to_level = {
            'admin': 1, 'staff': 2, 'premium': 3, 'vip': 4, 'white': 5, 'free': 6, 'user': 6
        }
        level_id = role_to_level.get(role.lower(), 6)

        if self.supabase.is_active:
            try:
                data = {
                    "telegram_id": telegram_id,
                    "role": role.lower(),
                    "level_id": level_id
                }
                if expires_at: data["expires_at"] = expires_at.isoformat()
                if custom_status: data["custom_status"] = custom_status
                if created_by: data["created_by"] = created_by
                if nickname: data["nickname"] = nickname
                
                self.supabase.get_client().table('users').upsert(data).execute()
                
                if role.lower() == 'admin':
                    self.supabase.get_client().table('admins').upsert({"user_id": telegram_id, "granted_by": created_by}).execute()
                else:
                    self.supabase.get_client().table('admins').delete().eq('user_id', telegram_id).execute()
                    
                return {"telegram_id": telegram_id, "role": role}
            except Exception as e:
                logger.error(f"Supabase upsert error: {e}")

        async with self.db.connection() as conn:
            # Check existence
            cursor = await conn.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            exists = await cursor.fetchone()

            if exists:
                fields = ["role = ?", "level_id = ?"]
                params = [role, level_id]
                if expires_at is not None:
                    fields.append("expires_at = ?")
                    params.append(expires_at)
                if custom_status is not None:
                    fields.append("custom_status = ?")
                    params.append(custom_status)
                if created_by is not None:
                    fields.append("created_by = ?")
                    params.append(created_by)
                if nickname is not None:
                    fields.append("nickname = ?")
                    params.append(nickname)

                params.append(telegram_id)
                sql = f"UPDATE users SET {', '.join(fields)} WHERE telegram_id = ?"
                await conn.execute(sql, tuple(params))
            else:
                await conn.execute(
                    "INSERT INTO users (telegram_id, role, level_id, added_at, expires_at, custom_status, created_by, nickname, settings) VALUES (?, ?, ?, ?, ?, ?, ?, ?, '{}')",
                    (
                        telegram_id,
                        role,
                        level_id,
                        datetime.utcnow(),
                        expires_at,
                        custom_status,
                        created_by,
                        nickname,
                    ),
                )

            # Sync with admins table
            if role.lower() == 'admin':
                await conn.execute(
                    "INSERT OR IGNORE INTO admins (user_id, granted_by) VALUES (?, ?)",
                    (telegram_id, created_by)
                )
            elif exists:
                await conn.execute("DELETE FROM admins WHERE user_id = ?", (telegram_id,))

            await conn.commit()
            return {"telegram_id": telegram_id, "role": role}

    async def update_status(self, telegram_id: int, custom_status: Optional[str]):
        if self.supabase.is_active:
            try:
                self.supabase.get_client().table('users').update({"custom_status": custom_status}).eq('telegram_id', telegram_id).execute()
            except Exception as e:
                logger.error(f"Supabase status error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET custom_status = ? WHERE telegram_id = ?",
                (custom_status, telegram_id),
            )
            await conn.commit()

    async def get_by_role(self, role: str) -> list[Dict[str, Any]]:
        results = []
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT telegram_id, role, expires_at FROM users WHERE role = ?",
                (role,),
            )
            rows = await cursor.fetchall()
            for row in rows:
                telegram_id, r, expires_raw = row
                results.append(
                    {
                        "telegram_id": telegram_id,
                        "role": r,
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
        if self.supabase.is_active:
            try:
                # Use RPC or multi-table select if possible, but simplest is two calls or a view
                # For now, let's join in Supabase
                res = self.supabase.get_client().table('users').select("*, level:user_levels(*)").eq('telegram_id', telegram_id).execute()
                if res.data:
                    user = res.data[0]
                    lvl = user.get('level', {})
                    is_admin = (user.get('role') == 'admin')
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
                            "price": lvl.get('price')
                        },
                        "hasAccess": bool(lvl.get('has_mini_app_access')) or is_admin,
                        "isAdmin": is_admin,
                        "isBetaTester": beta_tester
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
                (EXISTS(SELECT 1 FROM admins WHERE user_id = ?) OR u.role = 'admin') as is_admin,
                u.role
            FROM users u
            INNER JOIN user_levels ul ON u.level_id = ul.id
            WHERE u.telegram_id = ?
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(query, (telegram_id, telegram_id))
            row = await cursor.fetchone()
            if row:
                is_admin = bool(row[9])
                role = row[10] if len(row) > 10 else 'free'
                # For SQLite, treat admin and staff as beta testers 
                beta_tester = is_admin or role in ('admin', 'staff')
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
                        "price": row[8]
                    },
                    "hasAccess": bool(row[4]) or is_admin,  # Access if level allowed OR if admin
                    "isAdmin": is_admin,
                    "isBetaTester": beta_tester
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
                        "role": 'free',
                        "nickname": nickname
                    }).execute()
            except Exception as e:
                logger.error(f"Supabase create_minimal_user error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, level_id, role, added_at, nickname) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, level_id, 'free', datetime.utcnow(), nickname)
            )
            await conn.commit()

    async def get_all_levels(self) -> list[Dict[str, Any]]:
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_levels').select("*").order('priority', desc=True).execute()
                if res.data:
                    return [
                        {
                            "id": str(row['id']),
                            "name": row['name'],
                            "priority": row['priority'],
                            "color": row['color'],
                            "hasAccess": bool(row['has_mini_app_access']),
                            "dailyDownloads": row['daily_downloads'],
                            "earlyAccess": bool(row['early_access']),
                            "customThemes": bool(row['custom_themes']),
                            "price": row['price']
                        }
                        for row in res.data
                    ]
            except Exception as e:
                logger.error(f"Supabase get_all_levels error: {e}")

        """
        Retorna todos los niveles configurados con sus límites y características.
        """
        query = "SELECT id, name, priority, color, has_mini_app_access, daily_downloads, early_access, custom_themes, price FROM user_levels ORDER BY priority DESC"
        async with self.db.connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "priority": row[2],
                    "color": row[3],
                    "hasAccess": bool(row[4]),
                    "dailyDownloads": row[5],
                    "earlyAccess": bool(row[6]),
                    "customThemes": bool(row[7]),
                    "price": row[8]
                }
                for row in rows
            ]

    async def list_users(self, limit: int = 50, offset: int = 0, search: str = None) -> list[Dict[str, Any]]:
        if self.supabase.is_active:
            try:
                query = self.supabase.get_client().table('users').select("*, level:user_levels(name, color, daily_downloads)")
                if search:
                    # Supabase doesn't support easy OR complex filters via wrapper as nicely, but we can try
                    query = query.or_(f"nickname.ilike.%{search}%,telegram_id.eq.{search}")
                
                res = query.order('added_at', desc=True).range(offset, offset + limit - 1).execute()
                
                results = []
                for user in res.data:
                    lvl = user.get('level', {})
                    results.append({
                        "id": str(user['telegram_id']),
                        "username": user['nickname'] or f"User_{user['telegram_id']}",
                        "role": user['role'],
                        "level": {
                            "name": lvl.get('name') or "N/A",
                            "color": lvl.get('color') or "#888888"
                        },
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
                u.role, 
                ul.name as level_name, 
                ul.color as level_color,
                u.total_downloads,
                ul.daily_downloads
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
                tid, nickname, role, l_name, l_color, total_dl, daily_limit = row
                
                # Fetch downloads today from state_manager proxy if possible or just return a placeholder
                # In a real app we'd query download_history for today
                used_today = 0 # Placeholder, should be fetched per-user in a real scenario
                
                results.append({
                    "id": str(tid),
                    "username": nickname or f"User_{tid}",
                    "role": role,
                    "level": {
                        "name": l_name or "N/A",
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
        role = level_to_role.get(level_id, 'free')
        
        if self.supabase.is_active:
            try:
                self.supabase.get_client().table('users').update({
                    "level_id": level_id,
                    "role": role
                }).eq('telegram_id', telegram_id).execute()
                
                # Sync admins table in Supabase
                if role == 'admin':
                    self.supabase.get_client().table('admins').upsert({"user_id": telegram_id}).execute()
                else:
                    self.supabase.get_client().table('admins').delete().eq('user_id', telegram_id).execute()
            except Exception as e:
                logger.error(f"Supabase update_user_level error: {e}")

        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET level_id = ?, role = ? WHERE telegram_id = ?",
                (level_id, role, telegram_id)
            )
            # Sync admins table
            if role == 'admin':
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
            "price": "price",
            "name": "name",
            "color": "color"
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
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET settings = '{}' WHERE level_id = ?",
                (level_id,),
            )
            await conn.commit()

# Singleton instance
user_repo = UserRepository()
