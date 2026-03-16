from sqlalchemy import select

from models.library_models import Series
from repositories.base_repository import BaseRepository


class SeriesRepository(BaseRepository[Series]):
    """
    V4 Series Repository.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(Series, session=session, db_manager=db_manager)

    async def get_by_hash(self, series_hash: str) -> Series | None:
        """Busca una serie por su hash único."""
        stmt = select(Series).where(Series.hash == series_hash)
        async with self._get_session() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_title(self, title: str) -> Series | None:
        """Busca una serie por su título raw."""
        stmt = select(Series).where(Series.title_raw == title)
        async with self._get_session() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
