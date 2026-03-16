from sqlalchemy import select

from models.library_models import Book
from repositories.base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    """
    V4 Book Repository.
    """

    def __init__(self, session):
        super().__init__(Book, session)

    async def get_by_hash(self, book_hash: str) -> Book | None:
        """Busca un libro por su hash único."""
        stmt = select(Book).where(Book.hash == book_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_file_path(self, file_path: str) -> Book | None:
        """Busca un libro por su ruta de archivo."""
        stmt = select(Book).where(Book.file_path == file_path)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
