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
        """Obtiene los detalles completos de una serie (soporta búsqueda por prefijo)."""
        if len(series_id) < 64:
            return await self.series_repo.get_by_id_prefix(series_id)
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

    async def get_book_by_short_link(self, short_link: str) -> Book | None:
        """Busca un libro por su short_link."""
        return await self.book_repo.get_by_short_link(short_link)

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

    # --- Static Methods for v3.x compatibility ---

    @classmethod
    async def get_series_metadata(cls, series_hash: str) -> Series | None:
        """Obtiene metadata de una serie (Estático)."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            return await service.get_series_details(series_hash)

    @classmethod
    async def get_series_volumes(cls, series_hash: str, limit: int = 100, offset: int = 0) -> list[dict]:
        """Obtiene volúmenes de una serie (Estático)."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            books = await service.get_books_by_series(series_hash)
            # Aplicar paginación manual si es necesario, pero get_by_series ya devuelve todo
            # Convertir a dict para compatibilidad
            return [b.to_dict() for b in books]

    @classmethod
    async def get_series_total_downloads(cls, series_hash: str) -> int:
        """Obtiene el total de descargas de una serie (Estático)."""
        # TODO: Implementar contador real en la BD
        return 0

    @classmethod
    async def get_book_by_hash(cls, book_hash: str) -> dict | None:
        """Busca un libro por hash (Estático)."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            book = await service.book_repo.get_by_hash(book_hash)
            return book.to_dict() if book else None

    @classmethod
    async def search_series(
        cls, query: str = "", page: int = 1, items_per_page: int = 20, search_type: str = "todos", sort_by: str = "a-z"
    ) -> dict:
        """Busca series (Estático)."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            skip = (page - 1) * items_per_page
            items, total = await service.series_repo.search(
                query=query, sort_by=sort_by, skip=skip, limit=items_per_page
            )
            return {
                "results": [s.to_dict() for s in items],
                "totalItems": total,
                "page": page,
                "itemsPerPage": items_per_page,
                "totalPages": (total + items_per_page - 1) // items_per_page,
            }

    @classmethod
    async def get_recent_books(cls, page: int = 1, items_per_page: int = 10) -> dict:
        """Obtiene libros recientes."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            skip = (page - 1) * items_per_page
            books, total = await service.book_repo.get_all_paginated(skip=skip, limit=items_per_page)
            return {
                "items": [b.to_dict() for b in books],
                "totalItems": total,
                "totalPages": (total + items_per_page - 1) // items_per_page,
            }

    @classmethod
    async def get_genres(cls) -> list[str]:
        """Obtiene lista de géneros."""
        # TODO: Implementar en repo
        return ["Acción", "Aventura", "Comedia", "Drama", "Fantasía", "Romance", "Recuentos de la vida", "Sci-Fi"]
