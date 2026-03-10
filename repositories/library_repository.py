from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.library_models import Book, Series

from .base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    """
    CRUD for Books.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Book, session)

    async def get_by_hash(self, book_hash: str) -> Book | None:
        """Returns a book by its immutable hash."""
        stmt = select(Book).where(Book.book_hash == book_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_series(self, series_id: int) -> Sequence[Book]:
        """Returns all books belonging to a specific series."""
        stmt = select(Book).where(Book.series_id == series_id).order_by(Book.volume)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SeriesRepository(BaseRepository[Series]):
    """
    CRUD for Series.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Series, session)

    async def get_by_hash(self, series_hash: str) -> Series | None:
        """Returns a series by its immutable hash."""
        stmt = select(Series).where(Series.series_hash == series_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Series | None:
        """Returns a series by its persistent slug."""
        stmt = select(Series).where(Series.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_name(self, name_query: str, limit: int = 10) -> Sequence[Series]:
        """Performs a basic ILIKE search on series names."""
        stmt = (
            select(Series)
            .where(
                Series.series_name.ilike(f"%{name_query}%")
                | Series.series_english.ilike(f"%{name_query}%")
                | Series.series_spanish.ilike(f"%{name_query}%")
            )
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()
