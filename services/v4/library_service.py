from typing import Any

from sqlalchemy import func, or_, select

from models.library_models import Book, Series
from repositories.book_repository import BookRepository
from repositories.series_repository import SeriesRepository

from .base_service import BaseService


class LibraryService(BaseService):
    """
    V4 Business Logic for managing the Library.
    Orchestrates BookRepository and SeriesRepository.
    """

    async def get_series_catalog(
        self, page: int = 1, page_size: int = 20, sort_by: str = "title_asc"
    ) -> dict[str, Any]:
        """Catálogo paginado de Series."""
        async with self.db.get_session() as session:
            sort_map = {
                "title_asc": Series.series_name.asc(),
                "title_desc": Series.series_name.desc(),
                "updated_desc": Series.updated_at.desc(),
                "created_desc": Series.created_at.desc(),
            }
            order_by = sort_map.get(sort_by, Series.series_name.asc())

            count_stmt = select(func.count()).select_from(Series)
            total_items = (await session.execute(count_stmt)).scalar() or 0

            stmt = select(Series).order_by(order_by).offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(stmt)
            series_list = result.scalars().all()

            items = [self._map_series(s) for s in series_list]
            return {
                "items": items,
                "total": total_items,
                "page": page,
                "totalPages": (total_items + page_size - 1) // page_size if page_size > 0 else 0,
                "type": "series",
            }

    async def search_series(self, query: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """Búsqueda ILIKE en nombres (español, inglés, original) y autor."""
        async with self.db.get_session() as session:
            term = f"%{query}%"
            where = or_(
                Series.series_name.ilike(term),
                Series.series_spanish.ilike(term),
                Series.series_english.ilike(term),
                Series.author.ilike(term),
            )

            count_stmt = select(func.count()).select_from(Series).where(where)
            total_items = (await session.execute(count_stmt)).scalar() or 0

            stmt = (
                select(Series)
                .where(where)
                .order_by(Series.series_name.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result = await session.execute(stmt)
            items = [self._map_series(s) for s in result.scalars().all()]

            return {
                "items": items,
                "total": total_items,
                "page": page,
                "totalPages": (total_items + page_size - 1) // page_size if page_size > 0 else 0,
            }

    async def get_books_in_series(self, series_id: int) -> list[dict[str, Any]]:
        """Volúmenes de una serie ordenados por número de volumen."""
        async with self.db.get_session() as session:
            book_repo = BookRepository(session)
            books = await book_repo.get_by_series(series_id)
            return [self._map_book(b) for b in books]

    async def get_book_by_hash(self, book_hash: str) -> dict[str, Any] | None:
        """Busca un libro por su hash inmutable."""
        async with self.db.get_session() as session:
            book_repo = BookRepository(session)
            book = await book_repo.get_by_hash(book_hash)
            return self._map_book(book) if book else None

    async def get_series_by_hash(self, series_hash: str) -> dict[str, Any] | None:
        """Busca una serie por su hash inmutable."""
        async with self.db.get_session() as session:
            series_repo = SeriesRepository(session)
            s = await series_repo.get_by_hash(series_hash)
            return self._map_series(s) if s else None

    # ------------------------------------------------------------------ #
    #  Mappers internos                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _map_series(s: Series) -> dict[str, Any]:
        return {
            "id": f"series_{s.series_hash}",
            "title": s.series_name,
            "series_name": s.series_name,
            "series_spanish": s.series_spanish,
            "series_english": s.series_english,
            "series_hash": s.series_hash,
            "author": s.author,
            "cover": s.cover_url or "/book-placeholder.jpg",
            "book_type": s.book_type or "novel",
            "is_folder": True,
        }

    @staticmethod
    def _map_book(b: Book) -> dict[str, Any]:
        return {
            "id": b.id,
            "book_hash": b.book_hash,
            "title": b.title,
            "volume": float(b.volume) if b.volume is not None else 0.0,
            "language": b.language,
            "file_size": b.file_size,
            "filepath": b.filepath,
            "filename": b.filename,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "coverUrl": b.cover_medium or b.cover_low or "/book-placeholder.jpg",
        }

    # ------------------------------------------------------------------ #
    #  Ingesta de nuevos libros (UploadHandler)                           #
    # ------------------------------------------------------------------ #

    async def ingest_book(self, book_data: dict[str, Any]) -> dict[str, Any]:
        """
        Persiste un nuevo libro en la BD a partir de los datos del UploadHandler.

        Flujo:
          1. Obtener o crear la Serie por series_name + series_english
          2. Generar book_hash desde filepath (sha256)
          3. Crear el Book vinculado a la serie
          4. Devolver DTO del libro creado

        Args:
            book_data: dict con title, filepath, filename, file_size,
                       volume, language, series_name, series_english,
                       book_type, genres, description.
        """
        import hashlib

        async with self.db.get_session() as session:
            series_repo = SeriesRepository(session)
            book_repo = BookRepository(session)

            # 1. Obtener o crear la Serie
            series_name: str = book_data.get("series_name") or book_data.get("series_english") or "Sin serie"
            series_english: str = book_data.get("series_english") or series_name

            # Generar series_hash determinístico desde el nombre normalizado
            series_hash = hashlib.sha256(series_name.lower().strip().encode()).hexdigest()[:16]
            series = await series_repo.get_by_hash(series_hash)

            if not series:
                series = Series(
                    series_name=series_name,
                    series_spanish=series_name,
                    series_english=series_english,
                    series_hash=series_hash,
                    book_type=book_data.get("book_type", "novel"),
                    description=book_data.get("description"),
                )
                series = await series_repo.create(series)
                self.logger.info(f"[INGEST] Nueva serie: '{series_name}' hash={series_hash}")
            else:
                self.logger.info(f"[INGEST] Serie existente: '{series.series_name}' id={series.id}")

            # 2. Generar book_hash desde filepath (inmutable)
            filepath: str = book_data["filepath"]
            book_hash = hashlib.sha256(filepath.encode()).hexdigest()[:24]

            # 3. Verificar si ya existe (deduplication)
            existing = await book_repo.get_by_hash(book_hash)
            if existing:
                self.logger.info(f"[INGEST] Libro ya existe (hash={book_hash}), actualizando metadatos...")
                existing.title = book_data.get("title") or existing.title
                existing.volume = book_data.get("volume", existing.volume)
                existing.file_size = book_data.get("file_size", existing.file_size)
                await session.flush()
                return self._map_book(existing)

            # 4. Crear el Book
            book = Book(
                title=book_data.get("title") or series_name,
                book_hash=book_hash,
                filepath=filepath,
                filename=book_data["filename"],
                file_size=book_data.get("file_size", 0),
                volume=book_data.get("volume", 0.0),
                language=book_data.get("language", "es"),
                series_id=series.id,
                series_hash=series_hash,
            )
            book = await book_repo.create(book)
            self.logger.info(f"[INGEST] Libro creado: '{book.title}' hash={book_hash}")
            return self._map_book(book)
