from sqlalchemy import select

from models.library import Book, Series, Genre
from repositories.base import BaseRepository


class SeriesRepository(BaseRepository[Series]):
    def __init__(self, session):
        super().__init__(Series, session)

    async def get_by_slug(self, slug: str) -> Series | None:
        """Busca una serie por su slug."""
        query = select(Series).where(Series.slug == slug)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str = "",
        tag: str = None,
        author: str = None,
        sort_by: str = "a-z",
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Series], int]:
        """
        Busca series con filtros avanzados.
        Retorna (lista_de_series, total_count).
        """
        from sqlalchemy import func, or_

        stmt = select(Series)

        # Filtros
        if query:
            search = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Series.series_name.ilike(search),
                    Series.series_spanish.ilike(search),
                    Series.series_english.ilike(search),
                )
            )

        if tag:
            # Filtramos por el nombre del tag/género en la relación many-to-many
            stmt = stmt.where(Series.genres.any(Genre.name.ilike(tag)))

        if author:
            stmt = stmt.where(Series.author.ilike(f"%{author}%"))

        # Ordenación
        if sort_by == "newest":
            stmt = stmt.order_by(Series.created_at.desc())
        elif sort_by == "rating":
            stmt = stmt.order_by(Series.rating_avg.desc())
        else:
            stmt = stmt.order_by(Series.series_name.asc())

        # Contar total antes de paginar
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.execute(count_stmt)
        total_count = total.scalar_one()

        # Paginar
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        series_list = list(result.scalars().all())

        # Fallback de Búsqueda Difusa en Memoria si SQL no devolvió nada
        if not series_list and query and len(query) > 2:
            try:
                import difflib

                # Obtener todas las series para comparar en memoria
                all_stmt = select(Series)
                all_res = await self.session.execute(all_stmt)
                all_series = all_res.scalars().all()

                scored_series = []
                q_lower = query.lower()

                for s in all_series:
                    # Comparar contra nombre original, español e inglés
                    names_to_check = [
                        s.name,
                        s.name_spanish,
                        s.name_english,
                    ]
                    max_score = 0.0
                    for name in names_to_check:
                        if not name:
                            continue
                        name_lower = name.lower()

                        # 1. Coincidencia difusa rápida de ratio
                        ratio = difflib.SequenceMatcher(
                            None, q_lower, name_lower
                        ).ratio()

                        # 2. Si es substring, darle un bonus alto
                        if q_lower in name_lower or name_lower in q_lower:
                            ratio = max(ratio, 0.7)

                        if ratio > max_score:
                            max_score = ratio

                    # Umbral de coincidencia aceptable
                    if max_score >= 0.45:
                        scored_series.append((max_score, s))

                # Ordenar por score de mayor a menor
                scored_series.sort(key=lambda x: x[0], reverse=True)

                # Re-calcular total_count y paginar en memoria
                total_count = len(scored_series)
                sliced = scored_series[skip : skip + limit]

                series_list = []
                for score, s in sliced:
                    series_list.append(s)

            except Exception as fe:
                import logging

                logging.getLogger(__name__).error(
                    f"Error en fallback difuso de búsqueda de series: {fe}"
                )

        return series_list, total_count


class BookRepository(BaseRepository[Book]):
    def __init__(self, session):
        super().__init__(Book, session)

    async def get_by_hash(self, book_hash: str) -> Book | None:
        """Busca un libro por su hash."""
        return await self.get_by_id(book_hash)

    async def get_by_series(self, series_id: str) -> list[Book]:
        """Obtiene todos los libros de una serie."""
        query = select(Book).where(Book.series_id == series_id).order_by(Book.volume)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_short_link(self, short_link: str) -> Book | None:
        """Busca un libro por su short_link."""
        query = select(Book).where(Book.short_link == short_link)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
