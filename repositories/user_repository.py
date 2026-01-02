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

    async def get_by_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
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
        async with self.db.connection() as conn:
            # Check existence
            cursor = await conn.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            exists = await cursor.fetchone()

            # Mapping role to level_id
            role_to_level = {
                'admin': 1,
                'staff': 2,
                'premium': 3,
                'vip': 4,
                'white': 5,
                'free': 6,
                'user': 6
            }
            level_id = role_to_level.get(role.lower(), 6)

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
                    "INSERT INTO users (telegram_id, role, level_id, added_at, expires_at, custom_status, created_by, nickname) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
                # If it was an admin and now it's not
                await conn.execute("DELETE FROM admins WHERE user_id = ?", (telegram_id,))

            await conn.commit()
            return {"telegram_id": telegram_id, "role": role}

    async def update_status(self, telegram_id: int, custom_status: Optional[str]):
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
        async with self.db.connection() as conn:
            await conn.execute(
                "UPDATE users SET nickname = ? WHERE telegram_id = ?",
                (nickname, telegram_id),
            )
            await conn.commit()

    async def get_access_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de nivel y privilegios de admin para un usuario.
        """
        query = """
            SELECT
                ul.id,
                ul.name,
                ul.priority,
                ul.color,
                ul.has_mini_app_access,
                (EXISTS(SELECT 1 FROM admins WHERE user_id = ?) OR u.role = 'admin') as is_admin
            FROM users u
            INNER JOIN user_levels ul ON u.level_id = ul.id
            WHERE u.telegram_id = ?
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(query, (telegram_id, telegram_id))
            row = await cursor.fetchone()
            if row:
                return {
                    "level": {
                        "id": str(row[0]),
                        "name": row[1],
                        "priority": row[2],
                        "color": row[3],
                        "hasAccess": bool(row[4])
                    },
                    "hasAccess": bool(row[4]) or bool(row[5]),  # Access if level allowed OR if admin
                    "isAdmin": bool(row[5])
                }
            return None

    async def create_minimal_user(self, telegram_id: int, level_id: int = 6):
        """
        Crea un registro básico de usuario si no existe.
        Level 6 = Lector (default), role = 'free'
        """
        async with self.db.connection() as conn:
            await conn.execute(
                "INSERT OR IGNORE INTO users (telegram_id, level_id, role, added_at) VALUES (?, ?, ?, ?)",
                (telegram_id, level_id, 'free', datetime.utcnow())
            )
            await conn.commit()

    async def get_all_levels(self) -> list[Dict[str, Any]]:
        """
        Retorna todos los niveles configurados.
        """
        query = "SELECT id, name, priority, color, has_mini_app_access FROM user_levels ORDER BY priority DESC"
        async with self.db.connection() as conn:
            cursor = await conn.execute(query)
            rows = await cursor.fetchall()
            return [
                {
                    "id": str(row[0]),
                    "name": row[1],
                    "priority": row[2],
                    "color": row[3],
                    "hasAccess": bool(row[4])
                }
                for row in rows
            ]

    async def update_level_access(self, level_id: int, has_access: bool):
        """
        Actualiza el permiso de acceso a Mini App para un nivel.
        """
        query = "UPDATE user_levels SET has_mini_app_access = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        async with self.db.connection() as conn:
            await conn.execute(query, (1 if has_access else 0, level_id))
            await conn.commit()

    async def is_admin(self, telegram_id: int) -> bool:
        """
        Verifica si un usuario está en la tabla de admins.
        """
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


# Singleton instance
user_repo = UserRepository()
