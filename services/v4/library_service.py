import hashlib
import uuid
from typing import Any

from sqlalchemy import func, or_, select

from models.library_models import Book, Series
from repositories.v4 import BookRepository, SeriesRepository

from .base_service import BaseService


class LibraryService(BaseService):
    """
    V4 Business Logic for managing the Library.
    Orchestrates BookRepository and SeriesRepository V4.
    """

    async def get_series_catalog(
        self, page: int = 1, page_size: int = 20, sort_by: str = "title_asc"
    ) -> dict[str, Any]:
        """Catálogo paginado de Series V4."""
        async with self.db.get_session() as session:
            sort_map = {
                "title_asc": Series.title_raw.asc(),
                "title_desc": Series.title_raw.desc(),
                "updated_desc": Series.updated_at.desc(),
                "created_desc": Series.created_at.desc(),
            }
            order_by = sort_map.get(sort_by, Series.title_raw.asc())

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
        """Búsqueda ILIKE en nombres (español, original) y autor."""
        async with self.db.get_session() as session:
            term = f"%{query}%"
            where = or_(
                Series.title_raw.ilike(term),
                Series.title_spanish.ilike(term),
                # Series.author no existe en V4 schema as per schemas_v4.md?
                # Re-checking schemas_v4.md
            )

            count_stmt = select(func.count()).select_from(Series).where(where)
            total_items = (await session.execute(count_stmt)).scalar() or 0

            stmt = (
                select(Series)
                .where(where)
                .order_by(Series.title_raw.asc())
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
            "id": str(s.id),
            "title": s.title_raw,
            "title_spanish": s.title_spanish,
            "hash": s.hash,
            "cover": s.cover_url or "/book-placeholder.jpg",
            "is_folder": True,
        }

    @staticmethod
    def _map_book(b: Book) -> dict[str, Any]:
        return {
            "id": str(b.id),
            "hash": b.hash,
            "title": b.title,
            "volume": float(b.volume_number) if b.volume_number is not None else 0.0,
            "file_size": b.file_size,
            "file_path": b.file_path,
            "extension": b.extension,
            "created_at": b.created_at.isoformat() if b.created_at else None,
            "coverUrl": "/book-placeholder.jpg",  # V4 uses JSONB or dedicated fields for covers later
        }

    # ------------------------------------------------------------------ #
    #  Ingesta de nuevos libros (Invocado por ScannerServiceV4)           #
    # ------------------------------------------------------------------ #

    async def ingest_book(self, book_data: dict[str, Any]) -> dict[str, Any]:
        """
        Persiste un nuevo libro en la BD alineado al esquema V4.
        """
        async with self.db.get_session() as session:
            series_repo = SeriesRepository(session)
            book_repo = BookRepository(session)

            # 1. Obtener o crear la Serie
            # Mapeo flexible de títulos de serie
            series_title: str = (
                book_data.get("series")
                or book_data.get("series_title")
                or book_data.get("series_spanish")
                or "Sin serie"
            )
            source_id = book_data.get("source_id")
            if not source_id:
                raise ValueError("source_id is required for ingestion")

            # Generar hash determinístico para la serie (normalizado)
            series_hash = hashlib.sha256(series_title.lower().strip().encode()).hexdigest()[:16]
            series = await series_repo.get_by_hash(series_hash)

            if not series:
                series = Series(
                    hash=series_hash,
                    source_id=source_id,
                    title_raw=series_title,
                    title_spanish=book_data.get("series_spanish") or series_title,
                    status="reading",
                )
                print(f"[DEBUG] Creating series: {series_title}")
                series = await series_repo.create(series)
                self.logger.info(f"[INGEST-V4] Nueva serie: '{series_title}' hash={series_hash}")
            else:
                print(f"[DEBUG] Found series: {series.title_raw}")
                self.logger.info(f"[INGEST-V4] Serie existente: '{series.title_raw}' id={series.id}")

            # 2. Generar book_hash desde file_path (inmutable)
            file_path: str = book_data["file_path"]
            book_hash = hashlib.sha256(file_path.encode()).hexdigest()[:24]

            # 3. Verificar si ya existe (deduplication)
            existing = await book_repo.get_by_hash(book_hash)
            if existing:
                print(f"[DEBUG] Book exists: {book_hash}")
                self.logger.info(f"[INGEST-V4] Libro ya existe (hash={book_hash}), actualizando...")
                existing.title = book_data.get("title") or existing.title
                existing.volume_number = book_data.get("volume_number", existing.volume_number)
                existing.file_size = book_data.get("file_size", existing.file_size)
                await session.flush()
                return self._map_book(existing)

            # 4. Crear el Book
            print(f"[DEBUG] Creating book: {book_data.get('title') or series_title}")
            book = Book(
                id=uuid.uuid4(),
                series_id=series.id,
                hash=book_hash,
                file_path=file_path,
                file_size=book_data.get("file_size", 0),
                extension=book_data.get("extension", "epub"),
                volume_number=book_data.get("volume_number", 0.0),
                title=book_data.get("title") or series_title,
                is_published=False,
            )
            book = await book_repo.create(book)
            print(f"[DEBUG] Book created: {book.id}")
            self.logger.info(f"[INGEST-V4] Libro creado: '{book.title}' hash={book_hash}")
            return self._map_book(book)
