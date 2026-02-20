import logging
from typing import Any

from sqlalchemy import String, and_, cast, delete, func, or_, select
from sqlalchemy.orm import selectinload

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SeriesRepository(BaseRepository[SeriesMetadata]):
    """
    Repositorio para la gestión de metadatos de series (SeriesMetadata).
    """

    def __init__(self, db_manager=None):
        super().__init__(db_manager or pg_manager, "series_metadata")

    async def get_by_id(self, series_id: int) -> SeriesMetadata | None:
        async with pg_manager.get_session() as session:
            stmt = (
                select(SeriesMetadata).options(selectinload(SeriesMetadata.books)).where(SeriesMetadata.id == series_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_hash(self, series_hash: str) -> SeriesMetadata | None:
        """Busca una serie por su hash único."""
        async with pg_manager.get_session() as session:
            stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash == series_hash)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_name(self, series_name: str) -> SeriesMetadata | None:
        """Busca una serie por su nombre original."""
        async with pg_manager.get_session() as session:
            stmt = select(SeriesMetadata).where(SeriesMetadata.series_name == series_name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def list_series(self, page: int = 1, items_per_page: int = 20, sort_by: str = "name") -> dict[str, Any]:
        """Lista series paginadas."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(SeriesMetadata)

                # Conteo total
                count_stmt = select(func.count(SeriesMetadata.id))
                total_items = (await session.execute(count_stmt)).scalar() or 0

                # Orden y Paginación
                if sort_by == "name":
                    stmt = stmt.order_by(SeriesMetadata.series_name.asc())
                else:
                    stmt = stmt.order_by(SeriesMetadata.updated_at.desc())

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

    async def create(self, series: SeriesMetadata) -> SeriesMetadata:
        async with pg_manager.get_session() as session:
            session.add(series)
            await session.commit()
            await session.refresh(series)
            return series

    async def update(self, series_id: int, data: dict[str, Any]) -> bool:
        async with pg_manager.get_session() as session:
            series = await session.get(SeriesMetadata, series_id)
            if not series:
                return False

            for key, value in data.items():
                if hasattr(series, key):
                    setattr(series, key, value)

            await session.commit()
            return True

    async def delete(self, series_id: int) -> bool:
        async with pg_manager.get_session() as session:
            stmt = delete(SeriesMetadata).where(SeriesMetadata.id == series_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

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
        Búsqueda agrupada por series_hash de forma eficiente.
        """
        async with pg_manager.get_session() as session:
            try:
                pattern = f"%{query}%"

                # 1. Filtros para la serie
                series_filters = [
                    SeriesMetadata.series_name.ilike(pattern),
                    SeriesMetadata.series_spanish.ilike(pattern),
                    SeriesMetadata.series_english.ilike(pattern),
                    SeriesMetadata.author.ilike(pattern),
                ]

                # 2. Filtros para libros individuales (vía EXISTS)
                # Esto permite encontrar una serie si el nombre de un volumen coincide
                book_exists_filters = [
                    LocalBook.title.ilike(pattern),
                    LocalBook.filename.ilike(pattern),
                    LocalBook.translator.ilike(pattern),
                ]

                # Búsquedas por tags o demografía (campos JSON)
                if search_type in ("todos", "all", "genres", "géneros", "tags"):
                    series_filters.append(cast(SeriesMetadata.tags, String).ilike(pattern))
                    book_exists_filters.append(cast(LocalBook.tags, String).ilike(pattern))
                if search_type in ("todos", "all", "demographics", "demografía"):
                    series_filters.append(cast(SeriesMetadata.demographics, String).ilike(pattern))
                if search_type in ("translator", "traductor", "group", "grupo"):
                    book_exists_filters.append(LocalBook.translator.ilike(pattern))
                    # También buscamos en el campo publisher de la serie
                    series_filters.append(SeriesMetadata.publisher.ilike(pattern))

                # Construcción de la consulta con EXISTS para eficiencia
                from sqlalchemy import exists as sa_exists

                book_subq = sa_exists().where(
                    and_(
                        or_(
                            LocalBook.series_metadata_id == SeriesMetadata.id,
                            LocalBook.series_hash == SeriesMetadata.series_hash,
                        ),
                        or_(*book_exists_filters),
                    )
                )

                final_filters = [or_(*series_filters), book_subq]
                stmt = select(SeriesMetadata)

                if search_type in ("todos", "all"):
                    stmt = stmt.where(or_(*final_filters))
                else:
                    stmt = stmt.where(and_(*final_filters))

                if source_id:
                    stmt = (
                        stmt.join(
                            LocalBook,
                            or_(
                                LocalBook.series_metadata_id == SeriesMetadata.id,
                                LocalBook.series_hash == SeriesMetadata.series_hash,
                            ),
                        )
                        .where(LocalBook.source_id == source_id)
                        .distinct()
                    )

                # Ordenamiento
                if sort_by == "newest":
                    stmt = stmt.order_by(SeriesMetadata.id.desc())
                elif sort_by == "popular" or sort_by == "downloads":
                    stmt = stmt.order_by(SeriesMetadata.rating_count.desc())
                else:
                    stmt = stmt.order_by(SeriesMetadata.series_name.asc())

                # Conteo y Paginación
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_series = (await session.execute(count_stmt)).scalar() or 0

                start = (page - 1) * items_per_page
                stmt = stmt.offset(start).limit(items_per_page)

                res = await session.execute(stmt)
                series_list = res.scalars().all()

                # 4. Mapeo de DTOs y Datos Representativos
                results = []
                for s in series_list:
                    s_dict = s.to_dict()
                    results.append(s_dict)

                return {
                    "results": results,
                    "items": results,
                    "currentPage": page,
                    "totalPages": (total_series + items_per_page - 1) // items_per_page,
                    "totalItems": total_series,
                    "total": total_series,
                }
            except Exception as e:
                logger.error(f"Error en SeriesRepository.search_series: {e}")
                return {"results": [], "totalItems": 0}

    async def sync_book_count(self, series_hash: str) -> int:
        """Actualiza el contador de libros de una serie basado en los libros reales en DB."""
        async with pg_manager.get_session() as session:
            # Contar libros reales
            count_stmt = select(func.count(LocalBook.id)).where(LocalBook.series_hash == series_hash)
            real_count = (await session.execute(count_stmt)).scalar() or 0

            # Actualizar metadata
            stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash == series_hash)
            result = await session.execute(stmt)
            series = result.scalar_one_or_none()

            if series:
                series.book_count = real_count
                await session.commit()

            return real_count


# Instancia global
series_repo = SeriesRepository()
