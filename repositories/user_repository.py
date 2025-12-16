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
                "SELECT role, expires_at, custom_status, nickname FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            if row:
                role, expires_at_raw, custom_status, nickname = row
                expires_at = self._parse_datetime(expires_at_raw)
                return {
                    "telegram_id": telegram_id,
                    "role": role,
                    "expires_at": expires_at,
                    "custom_status": custom_status,
                    "nickname": nickname,
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

            if exists:
                fields = ["role = ?"]
                params = [role]
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
                    "INSERT INTO users (telegram_id, role, added_at, expires_at, custom_status, created_by, nickname) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        telegram_id,
                        role,
                        datetime.utcnow(),
                        expires_at,
                        custom_status,
                        created_by,
                        nickname,
                    ),
                )
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
