import logging
from typing import Any

from sqlalchemy import String, cast, delete, func, or_, select
from sqlalchemy.orm import selectinload

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata, UserDownload
from repositories.base_repository import BaseRepository
from schemas.library_schemas import BookDTO

logger = logging.getLogger(__name__)


class BookRepository(BaseRepository[LocalBook]):
    """
    Repositorio para la gestión de libros (LocalBook) en PostgreSQL.
    Implementa búsquedas optimizadas y acceso a metadatos.
    """

    def __init__(self, db_manager=None):
        super().__init__(db_manager or pg_manager, "local_books")

    async def get_by_id(self, book_id: int) -> LocalBook | None:
        """Obtiene un libro por ID con su información de serie cargada."""
        async with pg_manager.get_session() as session:
            stmt = select(LocalBook).options(selectinload(LocalBook.series_info)).where(LocalBook.id == book_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_hash(self, book_hash: str) -> LocalBook | None:
        """Busca un libro por su hash único."""
        async with pg_manager.get_session() as session:
            stmt = (
                select(LocalBook).options(selectinload(LocalBook.series_info)).where(LocalBook.book_hash == book_hash)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_filepath(self, filepath: str) -> LocalBook | None:
        """Busca un libro por su ruta de archivo."""
        async with pg_manager.get_session() as session:
            stmt = select(LocalBook).where(LocalBook.filepath == filepath)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def search_books(
        self,
        query: str,
        page: int = 1,
        items_per_page: int = 10,
        search_type: str = "all",
        source_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Realiza una búsqueda de libros utilizando PostgreSQL ILIKE (Async).
        Optimizado con subconsulta para conteo de descargas.
        """
        async with pg_manager.get_session() as session:
            try:
                pattern = f"%{query}%"

                # Filtros base
                filters = [
                    LocalBook.title.ilike(pattern),
                    SeriesMetadata.author.ilike(pattern),
                    SeriesMetadata.series_name.ilike(pattern),
                    SeriesMetadata.series_spanish.ilike(pattern),
                    SeriesMetadata.series_english.ilike(pattern),
                    LocalBook.romaji_title.ilike(pattern),
                    LocalBook.english_title.ilike(pattern),
                    LocalBook.spanish_title.ilike(pattern),
                ]

                # Filtros extendidos según el tipo de búsqueda
                if search_type in ("all", "todos", "genres", "géneros", "tags"):
                    filters.append(cast(SeriesMetadata.tags, String).ilike(pattern))
                if search_type in ("all", "todos", "demographics", "demografía"):
                    filters.append(cast(SeriesMetadata.demographics, String).ilike(pattern))
                if search_type in ("all", "todos", "translator", "traductor", "group", "grupo"):
                    filters.append(LocalBook.translator.ilike(pattern))
                if search_type in ("all", "todos", "illustrator", "ilustrador"):
                    # Fallback to checking author or related since illustrator was removed from LocalBook
                    filters.append(SeriesMetadata.author.ilike(pattern))
                if search_type in ("all", "todos", "layout", "maquetador", "typesetter"):
                    filters.append(LocalBook.layout_by.ilike(pattern))
                if search_type in ("all", "todos", "isbn"):
                    filters.append(LocalBook.isbn.ilike(pattern))

                # Subconsulta para conteo de descargas
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.book_hash == LocalBook.book_hash)
                    .correlate(LocalBook)
                    .scalar_subquery()
                )

                stmt = (
                    select(LocalBook, dl_subquery.label("download_count"))
                    .join(SeriesMetadata, LocalBook.series_metadata_id == SeriesMetadata.id)
                    .options(selectinload(LocalBook.series_info))
                    .where(or_(*filters))
                )

                if source_id:
                    stmt = stmt.where(LocalBook.source_id == source_id)

                # Contar total de resultados
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_items = (await session.execute(count_stmt)).scalar() or 0

                # Paginación y Orden
                start = (page - 1) * items_per_page
                stmt = stmt.order_by(LocalBook.title.asc()).offset(start).limit(items_per_page)

                result = await session.execute(stmt)
                rows = result.all()  # [(book, dl_count), ...]

                results = []
                for row in rows:
                    book, dl_count = row
                    book_dict = book.to_dict()
                    # Mapear a DTO para consistencia con el frontend
                    dto = BookDTO(
                        **book_dict,
                        download_count=dl_count or 0,
                        coverUrl=book.cover_medium or book.cover_low,
                    )
                    results.append(dto.model_dump())

                total_pages = (total_items + items_per_page - 1) // items_per_page

                return {
                    "results": results,
                    "items": results,
                    "currentPage": page,
                    "totalPages": total_pages,
                    "totalItems": total_items,
                }
            except Exception as e:
                logger.error(f"Error en search_books del repositorio: {e}")
                return {"results": [], "totalItems": 0, "totalPages": 0}

    async def get_recent_books(self, page: int = 1, items_per_page: int = 10) -> dict[str, Any]:
        """Obtiene los libros añadidos recientemente con soporte de paginación."""
        async with pg_manager.get_session() as session:
            # Subquery for download count
            dl_subquery = (
                select(func.count(UserDownload.id))
                .where(UserDownload.book_hash == LocalBook.book_hash)
                .correlate(LocalBook)
                .scalar_subquery()
            )

            stmt = select(LocalBook, dl_subquery.label("download_count")).options(selectinload(LocalBook.series_info))

            # Contar total de resultados
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_items = (await session.execute(count_stmt)).scalar() or 0

            # Paginación y Orden
            start = (page - 1) * items_per_page
            stmt = stmt.order_by(LocalBook.indexed_at.desc()).offset(start).limit(items_per_page)

            result = await session.execute(stmt)
            rows = result.all()

            results = []
            for row in rows:
                book, dl_count = row
                book_dict = book.to_dict()
                book_dict["download_count"] = dl_count or 0
                results.append(book_dict)

            total_pages = (total_items + items_per_page - 1) // items_per_page

            return {
                "results": results,
                "items": results,
                "currentPage": page,
                "totalPages": total_pages,
                "totalItems": total_items,
            }

    async def create(self, book: LocalBook) -> LocalBook:
        """Crea un nuevo libro en la base de datos."""
        from utils.helpers import generate_short_link

        if not book.short_link:
            book.short_link = generate_short_link()

        async with pg_manager.get_session() as session:
            session.add(book)
            await session.commit()
            await session.refresh(book)
            return book

    async def update(self, book_id: int, data: dict[str, Any]) -> bool:
        """Actualiza metadatos de un libro."""
        async with pg_manager.get_session() as session:
            book = await session.get(LocalBook, book_id)
            if not book:
                return False

            for key, value in data.items():
                if hasattr(book, key):
                    setattr(book, key, value)

            await session.commit()
            return True

    async def delete(self, book_id: int) -> bool:
        """Elimina un libro por ID."""
        async with pg_manager.get_session() as session:
            stmt = delete(LocalBook).where(LocalBook.id == book_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_total_downloads(self, book_hash: str) -> int:
        """Obtiene el conteo total de descargas para un hash de libro."""
        async with pg_manager.get_session() as session:
            stmt = select(func.count(UserDownload.id)).where(UserDownload.book_hash == book_hash)
            result = await session.execute(stmt)
            return result.scalar() or 0


# Instancia global
book_repo = BookRepository()
