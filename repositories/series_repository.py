import logging
from typing import Any

from sqlalchemy import String, and_, cast, delete, func, or_, select
from sqlalchemy.orm import selectinload

from models.library_models import Book, Series, UserDownload
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SeriesRepository(BaseRepository[Series]):
    """
    Repositorio para la gestión de metadatos de series (Series).
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(Series, session=session, db_manager=db_manager)

    async def get_by_id(self, id: Any) -> Series | None:
        """Obtiene una serie por su ID de base de datos."""
        async with self._get_session() as session:
            stmt = select(Series).options(selectinload(Series.books)).where(Series.id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    # create(), update() heredados son suficientes

    async def delete(self, id: Any) -> bool:
        """Elimina una serie por ID."""
        async with self._get_session() as session:
            stmt = delete(Series).where(Series.id == id)
            result = await session.execute(stmt)
            if not self.injected_session:
                await session.commit()
            return result.rowcount > 0

    async def get_by_hash(self, series_hash: str) -> Series | None:
        """Busca una serie por su hash único."""
        async with self._get_session() as session:
            stmt = select(Series).where(Series.series_hash == series_hash)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_name(self, series_name: str) -> Series | None:
        """Busca una serie por su nombre original."""
        async with self._get_session() as session:
            stmt = select(Series).where(Series.series_name == series_name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_series(self, page: int = 1, items_per_page: int = 20, sort_by: str = "name") -> dict[str, Any]:
        """Lista series paginadas."""
        async with self._get_session() as session:
            try:
                stmt = select(Series)

                # Conteo total
                count_stmt = select(func.count(Series.id))
                total_items = (await session.execute(count_stmt)).scalar() or 0

                # Orden y Paginación
                if sort_by == "name":
                    stmt = stmt.order_by(Series.series_name.asc())
                else:
                    stmt = stmt.order_by(Series.updated_at.desc())

                start = (page - 1) * items_per_page
                stmt = stmt.offset(start).limit(items_per_page)

                result = await session.execute(stmt)
                items = result.scalars().all()

                return {
                    "items": [i.to_dict() for i in items],
                    "totalItems": total_items,
                    "totalPages": (total_items + items_per_page - 1) // items_per_page,
                    "currentPage": page,
                }
            except Exception as e:
                logger.error(f"Error list_series: {e}")
                return {"items": [], "totalItems": 0, "totalPages": 0}

    async def update_data(self, series_id: int, data: dict[str, Any]) -> bool:
        """Actualiza campos específicos de una serie (Legacy/Helper)."""
        async with self._get_session() as session:
            series = await session.get(Series, series_id)
            if not series:
                return False

            for key, value in data.items():
                if hasattr(series, key):
                    setattr(series, key, value)

            await session.commit()
            return True

    async def search_series(
        self,
        query: str,
        page: int = 1,
        items_per_page: int = 20,
        source_id: int | None = None,
        search_type: str = "todos",
        sort_by: str = "a-z",
    ) -> dict[str, Any]:
        """
        Búsqueda agrupada por series de forma eficiente usando PostgreSQL.
        """
        async with self._get_session() as session:
            try:
                pattern = f"%{query}%"
                search_type = search_type.lower() if search_type else "todos"

                # Base query with download count subquery (DownloadLog no tiene series_hash; unir por book_hash → books)
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .select_from(UserDownload)
                    .join(Book, Book.book_hash == UserDownload.book_hash)
                    .where(Book.series_hash == Series.series_hash)
                    .correlate(Series)
                    .scalar_subquery()
                )

                stmt = select(Series, dl_subquery.label("download_count"))

                # 1. Filtros de Serie
                series_filters = []
                if search_type in ("todos", "all", "series", "serie", "título", "títulos"):
                    series_filters.extend(
                        [
                            Series.series_name.ilike(pattern),
                            Series.series_spanish.ilike(pattern),
                            Series.series_english.ilike(pattern),
                        ]
                    )

                if search_type in ("todos", "all", "author", "autor"):
                    series_filters.append(Series.author.ilike(pattern))

                if search_type in ("todos", "all", "tags", "géneros", "genres"):
                    series_filters.append(cast(Series.tags, String).ilike(pattern))

                if search_type in ("todos", "all", "demographics", "demografía"):
                    series_filters.append(cast(Series.demographics, String).ilike(pattern))

                if search_type in ("translator", "traductor", "group", "grupo"):
                    series_filters.append(Series.publisher.ilike(pattern))

                # 2. Filtros de Libro (vía EXISTS)
                book_filters = []
                if search_type in ("todos", "all", "maquetador", "layout", "typesetter"):
                    book_filters.append(Book.layout_by.ilike(pattern))

                if search_type in ("todos", "all", "traductor", "translator", "group", "grupo"):
                    book_filters.append(Book.translator.ilike(pattern))

                if search_type in ("todos", "all", "isbn"):
                    book_filters.append(Book.isbn.ilike(pattern))

                if search_type in ("todos", "all"):
                    # En modo 'todos', también buscamos título/filename en libros
                    book_filters.extend([Book.title.ilike(pattern), Book.filename.ilike(pattern)])

                # 3. Combinar filtros
                final_where = []
                if query:
                    if series_filters:
                        final_where.append(or_(*series_filters))

                    if book_filters:
                        from sqlalchemy import exists as sa_exists

                        book_subq = sa_exists().where(
                            and_(
                                or_(
                                    Book.series_id == Series.id,
                                    Book.series_hash == Series.series_hash,
                                ),
                                or_(*book_filters),
                            )
                        )
                        final_where.append(book_subq)

                if final_where:
                    if search_type in ("todos", "all"):
                        stmt = stmt.where(or_(*final_where))
                    else:
                        stmt = stmt.where(and_(*final_where))

                # 4. Filtro por Fuente
                if source_id:
                    stmt = (
                        stmt.join(
                            Book,
                            or_(
                                Book.series_id == Series.id,
                                Book.series_hash == Series.series_hash,
                            ),
                        )
                        .where(Book.source_id == source_id)
                        .distinct()
                    )

                # 5. Ordenamiento
                if sort_by == "newest":
                    stmt = stmt.order_by(Series.id.desc())
                elif sort_by in ("popular", "downloads"):
                    stmt = stmt.order_by(Series.rating_count.desc())
                else:
                    stmt = stmt.order_by(func.lower(Series.series_name).asc())

                # 6. Conteo y Paginación
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_series = (await session.execute(count_stmt)).scalar() or 0

                start = (page - 1) * items_per_page
                stmt = stmt.offset(start).limit(items_per_page)

                res = await session.execute(stmt)
                rows = res.all()
                series_list = []
                for row in rows:
                    s = row[0]
                    # Attach download_count attribute manually for the Service layer to use
                    s.download_count = row[1] or 0
                    series_list.append(s)

                return {
                    "results": series_list,
                    "items": series_list,
                    "currentPage": page,
                    "totalPages": (total_series + items_per_page - 1) // items_per_page,
                    "totalItems": total_series,
                    "total": total_series,
                }
            except Exception as e:
                logger.error(f"Error en SeriesRepository.search_series: {e}")
                return {"results": [], "totalItems": 0, "currentPage": page, "totalPages": 0}

    async def sync_book_count(self, series_hash: str) -> int:
        """Actualiza el contador de libros de una serie basado en los libros reales en DB."""
        async with self._get_session() as session:
            # Contar libros reales
            count_stmt = select(func.count(Book.id)).where(Book.series_hash == series_hash)
            real_count = (await session.execute(count_stmt)).scalar() or 0

            # Actualizar metadata
            stmt = select(Series).where(Series.series_hash == series_hash)
            result = await session.execute(stmt)
            series = result.scalar_one_or_none()

            if series:
                series.book_count = real_count
                await session.commit()

            return real_count


# Instancia global
series_repo = SeriesRepository()
