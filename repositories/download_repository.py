"""
repositories/download_repository.py
--------------------------------------
Repositorio de DownloadLog para tracking y rate limiting de descargas.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from models.user_models import DownloadLog

from .base_repository import BaseRepository


class DownloadRepository(BaseRepository[DownloadLog]):
    """
    CRUD para DownloadLog.
    Gestiona el registro de descargas y la consulta de límites diarios.
    """

    def __init__(self, db_manager=None):
        super().__init__(DownloadLog, db_manager=db_manager)

    async def count_today(self, telegram_id: int) -> int:
        """Cuenta las descargas del usuario desde las 00:00 UTC de hoy."""
        today_utc = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        async with self._get_session() as session:
            stmt = (
                select(func.count())
                .select_from(DownloadLog)
                .where(
                    DownloadLog.telegram_id == telegram_id,
                    DownloadLog.downloaded_at >= today_utc,
                )
            )
            result = await session.execute(stmt)
            return result.scalar() or 0

    async def log_download(
        self,
        telegram_id: int,
        book_hash: str,
        book_title: str | None = None,
        chat_id: int | None = None,
        series_hash: str | None = None,
    ) -> DownloadLog:
        """Registra una nueva descarga."""
        async with self._get_session() as session:
            entry = DownloadLog(
                telegram_id=telegram_id,
                book_hash=book_hash,
                book_title=book_title,
                chat_id=chat_id,
                series_hash=series_hash,
            )
            session.add(entry)
            await session.commit()
            await session.refresh(entry)
            return entry

    async def add_download(self, **kwargs) -> DownloadLog:
        """
        Alias para log_download compatible con V3.
        Mapea campos extendidos a los campos del modelo V4.
        """
        # Extraer campos que sí existen en V4
        telegram_id = kwargs.get("user_id") or kwargs.get("telegram_id")
        if not telegram_id:
            raise ValueError("telegram_id/user_id is required")

        book_hash = kwargs.get("book_hash")
        book_title = kwargs.get("title") or kwargs.get("book_title")
        chat_id = kwargs.get("chat_id")
        series_hash = kwargs.get("series_hash")

        # El modelo V4/TimestampedBase usa default para created_at/downloaded_at
        return await self.log_download(
            telegram_id=telegram_id,
            book_hash=book_hash,
            book_title=book_title,
            chat_id=chat_id,
            series_hash=series_hash,
        )

    async def get_recent(self, telegram_id: int, days: int = 7) -> list[DownloadLog]:
        """Devuelve las descargas recientes de un usuario."""
        since = datetime.now(UTC) - timedelta(days=days)
        async with self._get_session() as session:
            stmt = (
                select(DownloadLog)
                .where(
                    DownloadLog.telegram_id == telegram_id,
                    DownloadLog.downloaded_at >= since,
                )
                .order_by(DownloadLog.downloaded_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_user_downloads(self, telegram_id: int, limit: int = 20) -> list[DownloadLog]:
        """Descargas del usuario (para historial). Alias usado por api/handlers/downloads."""
        async with self._get_session() as session:
            stmt = (
                select(DownloadLog)
                .where(DownloadLog.telegram_id == telegram_id)
                .order_by(DownloadLog.downloaded_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())


download_repo = DownloadRepository()
