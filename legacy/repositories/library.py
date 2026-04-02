from sqlalchemy import select

from models.library import Book, Series
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
            # Asumimos que genres es una relación y queremos filtrar por ella
            # Pero para v4.0, a veces se guarda como JSON o relación many-to-many
            # Revisando model library: Series.genres es relación selectin
            # Filtramos por el nombre del tag en la tabla de taxonomía si fuera necesario.
            # Por ahora, implementación simple basada en el nombre de la serie
            pass

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
        return result.scalars().all(), total_count


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
