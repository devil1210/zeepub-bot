import logging

from sqlalchemy.ext.asyncio import AsyncSession

from models.library import Book, Series
from repositories.library import BookRepository, SeriesRepository

logger = logging.getLogger(__name__)


class LibraryService:
    """
    Servicio para gestionar la lógica de negocio de la librería (Series y Libros).
    """

    _is_ai_scanning: bool = False

    def __init__(self, session: AsyncSession):
        self.series_repo = SeriesRepository(session)
        self.book_repo = BookRepository(session)
        self.session = session

    async def get_series_details(self, series_id: str) -> Series | None:
        """
        Obtiene los detalles de una serie con robustez extrema (ID, Prefijo, Slug o Nombre).
        Fundamental para evitar errores 404 tras migraciones de IDs.
        """
        if not series_id:
            return None

        # 1. Búsqueda por ID exacto (Hash 64)
        series = await self.series_repo.get_by_id(series_id)
        if series:
            return series

        # 2. Búsqueda por prefijo del ID (Típico de Mini App v3)
        if len(series_id) < 64:
            series = await self.series_repo.get_by_id_prefix(series_id)
            if series:
                return series

        # 3. Búsqueda por Slug
        series = await self.series_repo.get_by_slug(series_id)
        if series:
            return series

        # 4. Búsqueda por coincidencia de nombre exacto (Salvavidas)
        from sqlalchemy import select

        query = select(Series).where(Series.name == series_id).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

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
        from sqlalchemy import func, select
        from core.db_manager_pg import pg_manager
        from models.library import UserDownload

        try:
            async with pg_manager.get_session() as session:
                service = cls(session)
                books = await service.get_books_by_series(series_hash)

                # Obtener descargas de todos los libros de esta serie agrupadas por book_hash
                book_hashes = [b.id for b in books]
                dl_map = {}
                if book_hashes:
                    dl_stmt = (
                        select(UserDownload.book_hash, func.count(UserDownload.id))
                        .where(UserDownload.book_hash.in_(book_hashes))
                        .group_by(UserDownload.book_hash)
                    )
                    dl_res = await session.execute(dl_stmt)
                    dl_map = {row[0]: row[1] for row in dl_res.all() if row[0]}

                # Convertir a dict y poblar download_count
                res = []
                for b in books:
                    b_dict = b.to_dict()
                    b_dict["download_count"] = dl_map.get(b.id, 0)
                    res.append(b_dict)
                return res
        except Exception as e:
            logger.error(f"Error getting volumes for series {series_hash}: {e}")
            return []

    @classmethod
    async def get_series_total_downloads(cls, series_hash: str) -> int:
        """Obtiene el total de descargas de una serie (Estático)."""
        from sqlalchemy import func, select
        from core.db_manager_pg import pg_manager
        from models.library import UserDownload

        try:
            async with pg_manager.get_session() as session:
                stmt = select(func.count(UserDownload.id)).where(UserDownload.series_hash == series_hash)
                res = await session.execute(stmt)
                return res.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting total downloads for series {series_hash}: {e}")
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
    async def search_books(
        cls, query: str = "", page: int = 1, items_per_page: int = 10, search_type: str = "all"
    ) -> dict:
        """Busca libros individuales utilizando el repositorio optimizado v4 (Estático)."""
        from repositories.book_repository import book_repo

        return await book_repo.search_books(
            query=query, page=page, items_per_page=items_per_page, search_type=search_type
        )

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
