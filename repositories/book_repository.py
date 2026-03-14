import logging
from typing import Any

from sqlalchemy import String, cast, delete, func, or_, select, update
from sqlalchemy.orm import selectinload

from models.download_models import DownloadHistory
from models.library_models import Book, Series, UserDownload, UserRating
from repositories.base_repository import BaseRepository
from schemas.library_schemas import BookDTO

logger = logging.getLogger(__name__)


class BookRepository(BaseRepository[Book]):
    """
    Repositorio para la gestión de libros (Book) en PostgreSQL.
    Implementa búsquedas optimizadas y acceso a metadatos.
    """

    def __init__(self, db_manager=None):
        super().__init__(Book, db_manager)

    # --- Métodos abstractos de BaseRepository ---

    async def get_by_id(self, id: Any) -> Book | None:
        """Obtiene un libro por ID con su información de serie cargada."""
        async with self.db_manager.get_session() as session:
            stmt = select(Book).options(selectinload(Book.series)).where(Book.id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create(self, entity: Book) -> Book:
        """Persiste un nuevo libro con generación de short_link si es necesario."""
        from utils.helpers import generate_short_link

        if not entity.short_link:
            entity.short_link = generate_short_link()

        async with self.db_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Book) -> Book:
        """Actualiza un libro completo."""
        async with self.db_manager.get_session() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def delete(self, id: Any) -> bool:
        """Elimina un libro por ID manejando referencias en otras tablas."""
        async with self.db_manager.get_session() as session:
            try:
                # Actualizar referencias en otras tablas
                await session.execute(update(DownloadHistory).where(DownloadHistory.book_id == id).values(book_id=None))
                await session.execute(update(UserDownload).where(UserDownload.book_id == id).values(book_id=None))
                await session.execute(update(UserRating).where(UserRating.book_id == id).values(book_id=None))

                stmt = delete(Book).where(Book.id == id)
                result = await session.execute(stmt)
                await session.commit()
                return result.rowcount > 0
            except Exception as e:
                logger.error(f"Error deleting book {id}: {e}")
                await session.rollback()
                return False

    async def get_by_hash(self, book_hash: str) -> Book | None:
        """Busca un libro por su hash único."""
        async with self.db_manager.get_session() as session:
            stmt = select(Book).options(selectinload(Book.series)).where(Book.book_hash == book_hash)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_filepath(self, filepath: str) -> Book | None:
        """Busca un libro por su ruta de archivo."""
        async with self.db_manager.get_session() as session:
            stmt = select(Book).where(Book.filepath == filepath)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_one_by_attr(self, attr: str, value: Any) -> Book | None:
        """Busca un libro por un atributo dinámico."""
        async with self.db_manager.get_session() as session:
            if not hasattr(Book, attr):
                return None
            stmt = select(Book).where(getattr(Book, attr) == value).limit(1)
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
        async with self.db_manager.get_session() as session:
            try:
                pattern = f"%{query}%"

                # Filtros base
                filters = [
                    Book.title.ilike(pattern),
                    Series.author.ilike(pattern),
                    Series.series_name.ilike(pattern),
                    Series.series_spanish.ilike(pattern),
                    Series.series_english.ilike(pattern),
                    Book.romaji_title.ilike(pattern),
                    Book.english_title.ilike(pattern),
                    Book.spanish_title.ilike(pattern),
                ]

                # Filtros extendidos según el tipo de búsqueda
                if search_type in ("all", "todos", "genres", "géneros", "tags"):
                    filters.append(cast(Series.tags, String).ilike(pattern))
                if search_type in ("all", "todos", "demographics", "demografía"):
                    filters.append(cast(Series.demographics, String).ilike(pattern))
                if search_type in ("all", "todos", "translator", "traductor", "group", "grupo"):
                    filters.append(Book.translator.ilike(pattern))
                if search_type in ("all", "todos", "illustrator", "ilustrador"):
                    # Fallback to checking author or related since illustrator was removed from Book
                    filters.append(Series.author.ilike(pattern))
                if search_type in ("all", "todos", "layout", "maquetador", "typesetter"):
                    filters.append(Book.layout_by.ilike(pattern))
                if search_type in ("all", "todos", "isbn"):
                    filters.append(Book.isbn.ilike(pattern))

                # Subconsulta para conteo de descargas
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.book_hash == Book.book_hash)
                    .correlate(Book)
                    .scalar_subquery()
                )

                stmt = (
                    select(Book, dl_subquery.label("download_count"))
                    .join(Series, Book.series_metadata_id == Series.id)
                    .options(selectinload(Book.series))
                    .where(or_(*filters))
                )

                if source_id:
                    stmt = stmt.where(Book.source_id == source_id)

                # Contar total de resultados
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_items = (await session.execute(count_stmt)).scalar() or 0

                # Paginación y Orden
                start = (page - 1) * items_per_page
                stmt = stmt.order_by(Book.title.asc()).offset(start).limit(items_per_page)

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
        async with self.db_manager.get_session() as session:
            # Subquery for download count
            dl_subquery = (
                select(func.count(UserDownload.id))
                .where(UserDownload.book_hash == Book.book_hash)
                .correlate(Book)
                .scalar_subquery()
            )

            stmt = select(Book, dl_subquery.label("download_count")).options(selectinload(Book.series))

            # Contar total de resultados
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total_items = (await session.execute(count_stmt)).scalar() or 0

            # Paginación y Orden
            start = (page - 1) * items_per_page
            stmt = stmt.order_by(Book.indexed_at.desc()).offset(start).limit(items_per_page)

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

    async def get_duplicate_hashes(self) -> list[tuple[str, int]]:
        """Obtiene hashes duplicados y su conteo."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = (
                    select(Book.book_hash, func.count().label("count"))
                    .where(Book.book_hash.isnot(None))
                    .group_by(Book.book_hash)
                    .having(func.count() > 1)
                )
                result = await session.execute(stmt)
                return result.all()
            except Exception as e:
                logger.error(f"Error getting duplicate hashes: {e}")
                return []

    async def get_books_by_hash(self, book_hash: str) -> list[Book]:
        """Obtiene todos los libros que comparten un hash."""
        async with self.db_manager.get_session() as session:
            try:
                stmt = select(Book).where(Book.book_hash == book_hash).order_by(Book.indexed_at.asc())
                result = await session.execute(stmt)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting books by hash {book_hash}: {e}")
                return []

    async def get_total_downloads(self, book_hash: str) -> int:
        """Obtiene el conteo total de descargas para un hash de libro."""
        async with self.db_manager.get_session() as session:
            stmt = select(func.count(UserDownload.id)).where(UserDownload.book_hash == book_hash)
            result = await session.execute(stmt)
            return result.scalar() or 0


# Instancia global
book_repo = BookRepository()
