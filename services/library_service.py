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
    async def get_series_volumes(
        cls, series_hash: str, limit: int = 100, offset: int = 0
    ) -> list[dict]:
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
                stmt = select(func.count(UserDownload.id)).where(
                    UserDownload.series_hash == series_hash
                )
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
        cls,
        query: str = "",
        page: int = 1,
        items_per_page: int = 20,
        search_type: str = "todos",
        sort_by: str = "a-z",
    ) -> dict:
        """Busca series (Estático)."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            skip = (page - 1) * items_per_page

            # Mapear search_type a filtros específicos del repositorio
            search_args = {
                "sort_by": sort_by,
                "skip": skip,
                "limit": items_per_page,
            }
            if search_type == "author":
                search_args["author"] = query
            elif search_type == "genres":
                search_args["tag"] = query
            else:
                search_args["query"] = query

            items, total = await service.series_repo.search(**search_args)
            return {
                "results": [s.to_dict() for s in items],
                "totalItems": total,
                "page": page,
                "itemsPerPage": items_per_page,
                "totalPages": (total + items_per_page - 1) // items_per_page,
            }

    @classmethod
    async def search_books(
        cls,
        query: str = "",
        page: int = 1,
        items_per_page: int = 10,
        search_type: str = "all",
    ) -> dict:
        """Busca libros individuales utilizando el repositorio optimizado v4 (Estático)."""
        from repositories.book_repository import book_repo

        return await book_repo.search_books(
            query=query,
            page=page,
            items_per_page=items_per_page,
            search_type=search_type,
        )

    @classmethod
    async def get_recent_books(cls, page: int = 1, items_per_page: int = 10) -> dict:
        """Obtiene libros recientes."""
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = cls(session)
            skip = (page - 1) * items_per_page
            books, total = await service.book_repo.get_all_paginated(
                skip=skip, limit=items_per_page
            )
            return {
                "items": [b.to_dict() for b in books],
                "totalItems": total,
                "totalPages": (total + items_per_page - 1) // items_per_page,
            }

    @classmethod
    async def get_genres(cls) -> list[str]:
        """Obtiene lista de géneros."""
        # TODO: Implementar en repo
        return [
            "Acción",
            "Aventura",
            "Comedia",
            "Drama",
            "Fantasía",
            "Romance",
            "Recuentos de la vida",
            "Sci-Fi",
        ]

    @classmethod
    async def get_series_by_tag(
        cls, tag: str, page: int = 1, page_size: int = 10
    ) -> dict:
        """Obtiene series filtradas por tag/género."""
        res = await cls.search_series(
            query=tag, page=page, items_per_page=page_size, search_type="genres"
        )
        return {"items": res["results"], "total": res["totalItems"]}

    @classmethod
    async def get_series_by_author(
        cls, author: str, page: int = 1, page_size: int = 10
    ) -> dict:
        """Obtiene series filtradas por autor."""
        res = await cls.search_series(
            query=author, page=page, items_per_page=page_size, search_type="author"
        )
        return {"items": res["results"], "total": res["totalItems"]}

    @classmethod
    async def resolve_series_hash(cls, short_hash: str) -> str:
        """Resuelve el hash completo de una serie a partir de un prefijo de 16 caracteres."""
        if len(short_hash) == 64:
            return short_hash

        from core.db_manager_pg import pg_manager
        from models.library import Series
        from sqlalchemy import select

        async with pg_manager.get_session() as session:
            stmt = select(Series.id).where(Series.id.like(f"{short_hash}%")).limit(1)
            result = await session.execute(stmt)
            val = result.scalar_one_or_none()
            return val or short_hash

    @classmethod
    async def get_authors(cls, page: int = 1, page_size: int = 10) -> dict:
        """Obtiene la lista de autores únicos de forma paginada desde PostgreSQL."""
        from core.db_manager_pg import pg_manager
        from models.library import Series
        from sqlalchemy import select, func

        async with pg_manager.get_session() as session:
            stmt = (
                select(Series.author)
                .where(Series.author.isnot(None), Series.author != "")
                .distinct()
                .order_by(Series.author.asc())
            )
            count_stmt = select(func.count(func.distinct(Series.author))).where(
                Series.author.isnot(None), Series.author != ""
            )
            total = (await session.execute(count_stmt)).scalar() or 0

            start = (page - 1) * page_size
            stmt = stmt.offset(start).limit(page_size)

            result = await session.execute(stmt)
            authors = [r[0] for r in result.all()]

            return {
                "items": authors,
                "total": total,
            }

    @classmethod
    async def get_library_stats(cls) -> dict:
        """Obtiene estadísticas globales de la biblioteca (cantidad total de series y libros)."""
        from core.db_manager_pg import pg_manager
        from models.library import Book, Series
        from sqlalchemy import select, func

        try:
            async with pg_manager.get_session() as session:
                series_count_stmt = select(func.count(Series.id))
                books_count_stmt = select(func.count(Book.id))

                series_res = await session.execute(series_count_stmt)
                books_res = await session.execute(books_count_stmt)

                return {
                    "series_count": series_res.scalar() or 0,
                    "books_count": books_res.scalar() or 0,
                }
        except Exception as e:
            logger.error(
                f"Error al obtener estadísticas globales de la biblioteca: {e}"
            )
            return {"series_count": 0, "books_count": 0}

    @classmethod
    async def merge_series(
        cls, target_hash: str, source_hash: str, new_name: str | None = None
    ) -> bool:
        """
        Fusiona una serie secundaria (source_hash) dentro de una serie principal (target_hash).
        Re-vincula todos los libros, transfiere géneros, demografías y alias, y elimina la serie secundaria.
        """
        if not target_hash or not source_hash or target_hash == source_hash:
            return False

        from core.db_manager_pg import pg_manager
        from models.library import SeriesAlias, SeriesMetadata
        from services.maintenance.orchestrator import MaintenanceOrchestrator
        from sqlalchemy import func, select, text

        try:
            async with pg_manager.get_session() as session:
                target_stmt = select(SeriesMetadata).where(
                    SeriesMetadata.id == target_hash
                )
                source_stmt = select(SeriesMetadata).where(
                    SeriesMetadata.id == source_hash
                )

                target = (await session.execute(target_stmt)).scalar_one_or_none()
                source = (await session.execute(source_stmt)).scalar_one_or_none()

                if not target or not source:
                    logger.error(
                        f"Error fusionando series: target={target_hash}, source={source_hash} no encontrados"
                    )
                    return False

                if new_name and new_name.strip():
                    target.series_name = new_name.strip()

                # Registrar los nombres de la serie origen como alias en la serie destino
                source_names = {
                    source.name,
                    source.series_spanish,
                    source.series_english,
                    source.series_name,
                }
                for s_name in source_names:
                    if (
                        s_name
                        and s_name.strip()
                        and len(s_name.strip()) > 1
                        and s_name.strip().lower() != "unknown"
                    ):
                        stmt_ex = select(SeriesAlias).where(
                            func.lower(SeriesAlias.alias) == s_name.strip().lower()
                        )
                        ex_alias = (await session.execute(stmt_ex)).scalar_one_or_none()
                        if not ex_alias:
                            session.add(
                                SeriesAlias(series_id=target.id, alias=s_name.strip())
                            )

                # Re-vincular alias de la serie origen
                await session.execute(
                    text("""
                        UPDATE series_aliases 
                        SET series_id = :tid 
                        WHERE series_id = :sid 
                          AND LOWER(alias) NOT IN (SELECT LOWER(alias) FROM series_aliases WHERE series_id = :tid)
                    """),
                    {"tid": target.id, "sid": source.id},
                )
                await session.execute(
                    text("DELETE FROM series_aliases WHERE series_id = :sid"),
                    {"sid": source.id},
                )

                # Re-vincular libros
                await session.execute(
                    text("""
                        UPDATE books 
                        SET series_id = :tid,
                            series_english = :t_en,
                            series_spanish = :t_es,
                            romaji_title = :t_romaji
                        WHERE series_id = :sid
                    """),
                    {
                        "tid": target.id,
                        "sid": source.id,
                        "t_en": target.series_english,
                        "t_es": target.series_spanish,
                        "t_romaji": target.name,
                    },
                )

                # Borrar relaciones de la serie origen y luego la serie misma
                await session.execute(
                    text("DELETE FROM series_demographics WHERE series_id = :sid"),
                    {"sid": source.id},
                )
                await session.execute(
                    text("DELETE FROM series_genres WHERE series_id = :sid"),
                    {"sid": source.id},
                )
                await session.execute(
                    text("DELETE FROM series WHERE id = :sid"),
                    {"sid": source.id},
                )

                await session.commit()

                # Recalcular conteo de libros en la base de datos
                await session.execute(
                    text("""
                        UPDATE series s
                        SET book_count = (SELECT COUNT(*) FROM books b WHERE b.series_id = s.id)
                    """)
                )
                await session.commit()

            # Ejecutar tareas de mantenimiento en segundo plano
            await MaintenanceOrchestrator.run_tool("db_integrity")
            await MaintenanceOrchestrator.run_tool("slug_recalculate")
            return True

        except Exception as e:
            logger.error(f"Error en merge_series ({source_hash} -> {target_hash}): {e}")
            return False

    @classmethod
    async def add_series_alias(cls, series_id: str, alias: str) -> dict:
        """Agrega un alias manualmente a una serie."""
        if not series_id or not alias or len(alias.strip()) <= 1:
            return {"success": False, "message": "Alias o ID de serie inválido"}

        from core.db_manager_pg import pg_manager
        from models.library import SeriesAlias, SeriesMetadata
        from sqlalchemy import func, select

        clean_alias = alias.strip()
        try:
            async with pg_manager.get_session() as session:
                series = (
                    await session.execute(
                        select(SeriesMetadata).where(SeriesMetadata.id == series_id)
                    )
                ).scalar_one_or_none()
                if not series:
                    return {"success": False, "message": "Serie no encontrada"}

                existing = (
                    await session.execute(
                        select(SeriesAlias).where(
                            func.lower(SeriesAlias.alias) == clean_alias.lower()
                        )
                    )
                ).scalar_one_or_none()
                if existing:
                    if existing.series_id == series_id:
                        return {
                            "success": True,
                            "message": "El alias ya pertenece a esta serie",
                        }
                    return {
                        "success": False,
                        "message": f"El alias ya está asignado a otra serie (ID: {existing.series_id})",
                    }

                alias_obj = SeriesAlias(series_id=series_id, alias=clean_alias)
                session.add(alias_obj)
                await session.commit()
                return {"success": True, "alias_id": alias_obj.id, "alias": clean_alias}
        except Exception as e:
            logger.error(f"Error añadiendo alias '{alias}' a serie '{series_id}': {e}")
            return {"success": False, "message": str(e)}

    @classmethod
    async def delete_series_alias(cls, alias_id: int) -> dict:
        """Elimina un alias de la base de datos."""
        from core.db_manager_pg import pg_manager
        from models.library import SeriesAlias
        from sqlalchemy import delete

        try:
            async with pg_manager.get_session() as session:
                await session.execute(
                    delete(SeriesAlias).where(SeriesAlias.id == alias_id)
                )
                await session.commit()
                return {"success": True}
        except Exception as e:
            logger.error(f"Error eliminando alias ID {alias_id}: {e}")
            return {"success": False, "message": str(e)}
