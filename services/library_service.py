import logging

from sqlalchemy.ext.asyncio import AsyncSession

from models.library import Book, Series
from repositories.library import BookRepository, SeriesRepository

logger = logging.getLogger(__name__)


class LibraryService:
    """
    Servicio para gestionar la lógica de negocio de la librería (Series y Libros).
    """

    def __init__(self, session: AsyncSession):
        self.series_repo = SeriesRepository(session)
        self.book_repo = BookRepository(session)
        self.session = session

    async def get_series_details(self, series_id: str) -> Series | None:
        """Obtiene los detalles completos de una serie."""
        return await self.series_repo.get_by_id(series_id)

    async def get_series_by_slug(self, slug: str) -> Series | None:
        """Busca una serie por su slug (útil para Telegram/Web)."""
        return await self.series_repo.get_by_slug(slug)

    async def get_all_series(self, skip: int = 0, limit: int = 50) -> list[Series]:
        """Obtiene el catálogo de series."""
        return await self.series_repo.get_all(skip=skip, limit=limit)

    async def get_books_by_series(self, series_id: str) -> list[Book]:
        """Obtiene los volúmenes de una serie específica."""
        return await self.book_repo.get_by_series(series_id)

    async def create_or_update_series(self, series_data: dict) -> Series:
        """
        Crea o actualiza una serie basándose en su hash.
        Este método es el corazón del escaneo v4.0.
        """
        series_id = series_data.get("id")
        existing = await self.series_repo.get_by_id(series_id)

        if existing:
            # Lógica de actualización selectiva
            for key, value in series_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            return existing
        else:
            # Crear nueva serie
            return await self.series_repo.create(**series_data)

    async def register_book(self, book_data: dict) -> Book:
        """Registra un nuevo libro en la base de datos."""
        book_id = book_data.get("id")
        existing = await self.book_repo.get_by_id(book_id)

        if existing:
            # Actualizar si el filepath cambió o hay nueva metadata
            for key, value in book_data.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
            return existing
        else:
            return await self.book_repo.create(**book_data)

    async def commit_changes(self):
        """Persiste todos los cambios realizados en la sesión."""
        await self.session.commit()
