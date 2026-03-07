from typing import Optional, List
from sqlalchemy import select
from models.library import Series, Book
from repositories.base import BaseRepository

class SeriesRepository(BaseRepository[Series]):
    def __init__(self, session):
        super().__init__(Series, session)

    async def get_by_slug(self, slug: str) -> Optional[Series]:
        """Busca una serie por su slug."""
        query = select(Series).where(Series.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

class BookRepository(BaseRepository[Book]):
    def __init__(self, session):
        super().__init__(Book, session)

    async def get_by_hash(self, book_hash: str) -> Optional[Book]:
        """Busca un libro por su hash."""
        return await self.get_by_id(book_hash)

    async def get_by_series(self, series_id: str) -> List[Book]:
        """Obtiene todos los libros de una serie."""
        query = select(Book).where(Book.series_id == series_id).order_by(Book.volume)
        result = await self.session.execute(query)
        return result.scalars().all()
