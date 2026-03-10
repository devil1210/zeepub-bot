"""
repositories/download_repository.py
--------------------------------------
Repositorio de DownloadLog para tracking y rate limiting de descargas.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_models import DownloadLog

from .base_repository import BaseRepository


class DownloadRepository(BaseRepository[DownloadLog]):
    """
    CRUD para DownloadLog.
    Gestiona el registro de descargas y la consulta de límites diarios.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(DownloadLog, session)

    async def count_today(self, telegram_id: int) -> int:
        """Cuenta las descargas del usuario desde las 00:00 UTC de hoy."""
        today_utc = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        stmt = (
            select(func.count())
            .select_from(DownloadLog)
            .where(
                DownloadLog.telegram_id == telegram_id,
                DownloadLog.downloaded_at >= today_utc,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def log_download(
        self,
        telegram_id: int,
        book_hash: str,
        book_title: str | None = None,
        chat_id: int | None = None,
    ) -> DownloadLog:
        """Registra una nueva descarga."""
        entry = DownloadLog(
            telegram_id=telegram_id,
            book_hash=book_hash,
            book_title=book_title,
            chat_id=chat_id,
            downloaded_at=datetime.now(UTC),
        )
        return await self.create(entry)

    async def get_recent(self, telegram_id: int, days: int = 7) -> list[DownloadLog]:
        """Devuelve las descargas recientes de un usuario."""
        since = datetime.now(UTC) - timedelta(days=days)
        stmt = (
            select(DownloadLog)
            .where(
                DownloadLog.telegram_id == telegram_id,
                DownloadLog.downloaded_at >= since,
            )
            .order_by(DownloadLog.downloaded_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
