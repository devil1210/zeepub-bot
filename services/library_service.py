import logging
from typing import Any

from sqlalchemy import String, and_, cast, exists, func, or_, select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata, UserDownload
from schemas.library_schemas import BookDTO, CoverUrlDTO, SeriesDTO

logger = logging.getLogger(__name__)


class LibraryService:
    @staticmethod
    async def search_books(
        query: str,
        page: int = 1,
        items_per_page: int = 10,
        search_type: str = "all",
        source_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Realiza una búsqueda de libros utilizando PostgreSQL ILIKE (Async).
        Optimizado con subconsulta para conteo de descargas y validación Pydantic.
        """
        async with pg_manager.get_session() as session:
            try:
                pattern = f"%{query}%"

                # Filtros base
                filters = [
                    LocalBook.title.ilike(pattern),
                    LocalBook.author.ilike(pattern),
                    LocalBook.series.ilike(pattern),
                    LocalBook.series_spanish.ilike(pattern),
                    LocalBook.romaji_title.ilike(pattern),
                    LocalBook.english_title.ilike(pattern),
                    LocalBook.spanish_title.ilike(pattern),
                ]

                if search_type in ("all", "todos", "genres", "géneros", "tags"):
                    filters.append(cast(LocalBook.tags, String).ilike(pattern))
                if search_type in ("all", "todos", "demographics", "demografía"):
                    filters.append(cast(LocalBook.demographics, String).ilike(pattern))
                if search_type in ("all", "todos", "translator", "traductor", "group", "grupo"):
                    filters.append(LocalBook.translator.ilike(pattern))
                if search_type in ("all", "todos", "illustrator", "ilustrador"):
                    filters.append(LocalBook.illustrator.ilike(pattern))
                if search_type in ("all", "todos", "layout", "maquetador", "typesetter"):
                    filters.append(LocalBook.layout_by.ilike(pattern))
                if search_type in ("all", "todos", "isbn"):
                    filters.append(LocalBook.isbn.ilike(pattern))

                # Subquery for download count
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.book_hash == LocalBook.book_hash)
                    .correlate(LocalBook)
                    .scalar_subquery()
                )

                stmt = select(LocalBook, dl_subquery.label("download_count")).where(or_(*filters))

                if source_id:
                    stmt = stmt.where(LocalBook.source_id == source_id)

                # Count total
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_items = (await session.execute(count_stmt)).scalar() or 0

                # Pagination
                start = (page - 1) * items_per_page
                stmt = stmt.order_by(LocalBook.title.asc()).offset(start).limit(items_per_page)

                result = await session.execute(stmt)
                rows = result.all()  # [(book, dl_count), ...]

                results = []
                for row in rows:
                    b = row[0]
                    dl_count = row[1] or 0

                    b_dict = b.to_dict()

                    # Map to DTO
                    dto = BookDTO(**b_dict, download_count=dl_count, coverUrl=b.cover_low)
                    results.append(dto.model_dump())

                total_pages = (total_items + items_per_page - 1) // items_per_page

                return {
                    "results": results,
                    "items": results,
                    "currentPage": page,
                    "page": page,
                    "totalPages": total_pages,
                    "totalItems": total_items,
                    "total": total_items,
                }
            except Exception as e:
                logger.error(f"[LibraryService.search_books] Error: {e}")
                return {
                    "results": [],
                    "items": [],
                    "currentPage": page,
                    "page": page,
                    "totalPages": 0,
                    "totalItems": 0,
                    "total": 0,
                }

    @staticmethod
    async def search_series(
        query: str,
        page: int = 1,
        items_per_page: int = 20,
        source_id: int | None = None,
        search_type: str = "todos",
        sort_by: str = "a-z",
    ) -> dict[str, Any]:
        """
        Búsqueda agrupada por series_hash. Retorna un objeto similar a Series
        en lugar de volúmenes individuales (Exclusivo para PostgreSQL).
        """
        async with pg_manager.get_session() as session:
            try:
                pattern = f"%{query}%"
                # 1. Construcción dinámica de filtros y necesidad de Join

                search_type = search_type.lower() if search_type else "todos"

                # Base query
                stmt = select(SeriesMetadata)

                # Definimos filtros de serie
                series_filters = []
                if search_type in ("todos", "all", "series", "serie", "título", "títulos"):
                    series_filters.extend(
                        [
                            SeriesMetadata.series_name.ilike(pattern),
                            SeriesMetadata.series_spanish.ilike(pattern),
                        ]
                    )

                if search_type in ("todos", "all", "author", "autor"):
                    series_filters.append(SeriesMetadata.author.ilike(pattern))

                if search_type in ("todos", "all", "tags", "géneros", "genres"):
                    series_filters.append(cast(SeriesMetadata.tags, String).ilike(pattern))

                if search_type in ("todos", "all", "demographics", "demografía"):
                    series_filters.append(cast(SeriesMetadata.demographics, String).ilike(pattern))

                # Definimos filtros de libro
                book_filters = []
                if search_type in ("todos", "all", "maquetador", "layout", "typesetter"):
                    book_filters.append(LocalBook.layout_by.ilike(pattern))

                if search_type in ("todos", "all", "traductor", "translator", "group", "grupo"):
                    book_filters.append(LocalBook.translator.ilike(pattern))

                if search_type in ("todos", "all", "illustrator", "ilustrador"):
                    series_filters.append(
                        SeriesMetadata.illustrator.ilike(pattern)
                    )  # Check series level
                    book_filters.append(LocalBook.illustrator.ilike(pattern))  # Check book level

                if search_type in ("todos", "all", "isbn"):
                    book_filters.append(LocalBook.isbn.ilike(pattern))

                # Combinamos filtros
                final_filters = []
                if series_filters:
                    final_filters.append(or_(*series_filters))

                if book_filters:
                    # Agregamos condición EXISTS para los filtros de libros
                    # Join flexible: id de metadata o hash de serie
                    book_exists_filter = exists().where(
                        and_(
                            or_(
                                LocalBook.series_metadata_id == SeriesMetadata.id,
                                LocalBook.series_hash == SeriesMetadata.series_hash,
                            ),
                            or_(*book_filters),
                        )
                    )
                    final_filters.append(book_exists_filter)

                if final_filters:
                    # Si es búsqueda específica de libro (ej: maquetador), usamos AND para el EXISTS
                    # Si es 'todos', usamos OR entre filtros de serie y filtros de libro
                    if search_type in ("todos", "all"):
                        stmt = stmt.where(or_(*final_filters))
                    else:
                        # Si buscamos algo que solo está en libros, los filtros de serie estarán vacíos o no deben interferir
                        # final_filters tendrá el o_(*series_filters) if any, y el EXISTS.
                        # Para búsquedas específicas (ej: maquetador), solo queremos resultados que cumplan ese criterio.
                        stmt = stmt.where(and_(*final_filters))

                # Filtro por fuente (siempre requiere Join o EXISTS)
                if source_id:
                    # Para source_id, es preferible el Join porque usualmente filtramos TODO el catálogo por fuente
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

                # 3. Ordenamiento
                if sort_by == "newest":
                    stmt = stmt.order_by(SeriesMetadata.id.desc())
                elif sort_by == "popular":
                    stmt = stmt.order_by(SeriesMetadata.rating_count.desc())
                elif sort_by == "downloads":
                    stmt = stmt.order_by(SeriesMetadata.rating_count.desc())
                else:
                    stmt = stmt.order_by(SeriesMetadata.series_name.asc())

                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_series = (await session.execute(count_stmt)).scalar() or 0

                start = (page - 1) * items_per_page
                stmt = stmt.offset(start).limit(items_per_page)

                res = await session.execute(stmt)
                series_list = res.scalars().all()

                # Para evitar N+1 queries al mapear DTOs, obtenemos un libro representativo para cada serie en lote
                series_hashes = [s.series_hash for s in series_list]
                rep_books_map = {}
                if series_hashes:
                    # Buscamos el primer libro de cada serie para extraer metadatos extras (traductor, maquetador)
                    # Usamos una query que agrupa por series_hash y toma el primer libro

                    # Subconsulta para obtener el ID del primer libro por serie
                    subq = (
                        select(LocalBook.series_hash, func.min(LocalBook.id).label("min_id"))
                        .where(LocalBook.series_hash.in_(series_hashes))
                        .group_by(LocalBook.series_hash)
                        .subquery()
                    )

                    rep_stmt = select(LocalBook).join(subq, LocalBook.id == subq.c.min_id)
                    rep_res = await session.execute(rep_stmt)
                    for b in rep_res.scalars().all():
                        rep_books_map[b.series_hash] = b

                results = []
                for s in series_list:
                    rep = rep_books_map.get(s.series_hash)

                    # Map to DTO
                    dto = SeriesDTO(
                        id=f"series_{s.series_hash}",
                        series_hash=s.series_hash,
                        title=s.series_name,
                        series=s.series_name,
                        series_spanish=s.series_spanish,
                        author=s.author,
                        description=s.description,
                        cover=s.cover_url,
                        coverUrl=CoverUrlDTO(
                            cover_low=s.cover_url,
                            cover_medium=s.cover_url.replace("_low.jpg", "_medium.jpg")
                            if s.cover_url
                            else None,
                            cover_high=s.cover_url.replace("_low.jpg", "_high.jpg")
                            if s.cover_url
                            else None,
                            cover_original=s.cover_url.replace("_low.jpg", "_original.jpg")
                            if s.cover_url
                            else None,
                            cover=s.cover_url,
                        ),
                        numBooks=s.book_count,
                        book_type=s.book_type,
                        rating_average=s.rating_average,
                        rating_count=s.rating_count,
                        illustrator=s.illustrator or (rep.illustrator if rep else None),
                        translator=(rep.translator if rep else None),
                        layout_by=(rep.layout_by if rep else None),
                        lastUpdated=s.updated_at.isoformat() if s.updated_at else None,
                    )
                    results.append(dto.model_dump())

                return {
                    "results": results,
                    "currentPage": page,
                    "totalPages": (total_series + items_per_page - 1) // items_per_page,
                    "totalItems": total_series,
                }

            except Exception as e:
                logger.error(f"[LibraryService.search_series] Error: {e}")
                return {"results": [], "totalItems": 0}

    @staticmethod
    async def get_series_volumes(
        series_hash: str, limit: int | None = None, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Retorna los volúmenes de una serie agrupada (Async). Validado con Pydantic."""
        async with pg_manager.get_session() as session:
            try:
                # Subquery for download count per volume
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.book_hash == LocalBook.book_hash)
                    .correlate(LocalBook)
                    .scalar_subquery()
                )

                stmt = (
                    select(LocalBook, dl_subquery.label("download_count"))
                    .where(LocalBook.series_hash == series_hash)
                    .order_by(LocalBook.volume.asc())
                )

                if limit:
                    stmt = stmt.offset(offset).limit(limit)

                res = await session.execute(stmt)
                rows = res.all()

                results = []
                for row in rows:
                    b = row[0]
                    dl_count = row[1] or 0

                    b_dict = b.to_dict()

                    dto = BookDTO(**b_dict, download_count=dl_count, coverUrl=b.cover_low)
                    results.append(dto.model_dump())

                return results
            except Exception as e:
                logger.error(f"[LibraryService.get_series_volumes] Error: {e}")
                return []

    @staticmethod
    async def get_book_by_id(book_id: int) -> dict[str, Any] | None:
        """Busca un libro por su ID con validación Pydantic."""
        async with pg_manager.get_session() as session:
            try:
                # Subquery for DL count
                dl_subquery = (
                    select(func.count(UserDownload.id))
                    .where(UserDownload.book_hash == LocalBook.book_hash)
                    .correlate(LocalBook)
                    .scalar_subquery()
                )

                stmt = select(LocalBook, dl_subquery.label("download_count")).where(
                    LocalBook.id == book_id
                )
                res = await session.execute(stmt)
                row = res.one_or_none()

                if not row:
                    return None

                book = row[0]
                dl_count = row[1] or 0

                b_dict = book.to_dict()

                dto = BookDTO(**b_dict, download_count=dl_count, coverUrl=book.cover_low)
                return dto.model_dump()
            except Exception as e:
                logger.error(f"[LibraryService.get_book_by_id] Error: {e}")
                return None

    @staticmethod
    async def update_book_metadata(book_id: int, updates: dict[str, Any]) -> bool:
        """Actualiza metadatos de un libro y recalcula el hash de serie."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(LocalBook).where(LocalBook.id == book_id)
                result = await session.execute(stmt)
                book = result.scalar_one_or_none()

                if not book:
                    return False

                # Update allowed fields
                if "title" in updates:
                    book.title = updates["title"]
                if "author" in updates:
                    book.author = updates["author"]
                if "series" in updates:
                    book.series = updates["series"]
                if "volume" in updates:
                    try:
                        book.volume = float(updates["volume"])
                    except (ValueError, TypeError):
                        pass
                if "book_type" in updates:
                    book.book_type = updates["book_type"]
                if "romaji_title" in updates:
                    book.romaji_title = updates["romaji_title"]
                if "english_title" in updates:
                    book.english_title = updates["english_title"]
                if "tags" in updates:
                    book.tags = updates["tags"]
                if "demographics" in updates:
                    book.demographics = updates["demographics"]

                # Recalculate Series Hash to regroup
                from utils.helpers import generate_series_hash

                series_name = book.series or book.english_title or book.title
                book.series_hash = generate_series_hash(
                    series=series_name, author=book.author, book_type=book.book_type
                )

                await session.commit()
                return True
            except Exception as e:
                logger.error(f"[LibraryService.update_book_metadata] Error: {e}")
                return False

    @staticmethod
    async def get_regroup_suggestions(threshold: float = 0.8) -> list[dict[str, Any]]:
        """
        Analiza libros sin serie o con series diferentes y sugiere agrupaciones
        basadas en similitud de títulos y autor.
        """
        async with pg_manager.get_session() as session:
            try:
                # 1. Obtener libros sospechosos (sin series o series con 1 solo volumen)
                # Esta consulta simplificada obtiene libros sin serie asignda explícitamente
                stmt = (
                    select(LocalBook)
                    .where(or_(LocalBook.series.is_(None), LocalBook.series == ""))
                    .order_by(LocalBook.author, LocalBook.title)
                )

                result = await session.execute(stmt)
                books = result.scalars().all()

                # 2. Agrupamiento lógico simple en memoria (Python)
                from difflib import SequenceMatcher

                groups = []
                used_ids = set()

                for i, book_a in enumerate(books):
                    if book_a.id in used_ids:
                        continue

                    current_group = [book_a]
                    used_ids.add(book_a.id)

                    for _j, book_b in enumerate(books[i + 1 :], start=i + 1):
                        if book_b.id in used_ids:
                            continue

                        # Mismo autor es un requisito fuerte
                        if (
                            book_a.author
                            and book_b.author
                            and book_a.author.lower() != book_b.author.lower()
                        ):
                            continue

                        # Similitud de título
                        similarity = SequenceMatcher(None, book_a.title, book_b.title).ratio()
                        if similarity >= threshold:
                            current_group.append(book_b)
                            used_ids.add(book_b.id)

                    if len(current_group) > 1:
                        # Sugerencia encontrada
                        common_title = current_group[0].title
                        # Intentar extraer parte común
                        match = SequenceMatcher(
                            None, current_group[0].title, current_group[1].title
                        ).find_longest_match(
                            0,
                            len(current_group[0].title),
                            0,
                            len(current_group[1].title),
                        )
                        suggested_name = (
                            current_group[0]
                            .title[match.a : match.a + match.size]
                            .strip(" -:volume")
                        )

                        groups.append(
                            {
                                "suggested_series": suggested_name or common_title,
                                "confidence": "high",
                                "books": [b.to_dict() for b in current_group],
                            }
                        )

                return groups
            except Exception as e:
                logger.error(f"[LibraryService.get_regroup_suggestions] Error: {e}")
                return []

    @staticmethod
    async def get_books_without_series(limit: int = 100) -> list[dict[str, Any]]:
        """Retorna una lista simple de libros que no tienen serie asignada."""
        async with pg_manager.get_session() as session:
            try:
                stmt = (
                    select(LocalBook)
                    .where(or_(LocalBook.series.is_(None), LocalBook.series == ""))
                    .order_by(LocalBook.indexed_at.desc())
                    .limit(limit)
                )

                result = await session.execute(stmt)
                books = result.scalars().all()
                return [b.to_dict() for b in books]
            except Exception as e:
                logger.error(f"Error fetching orphaned books: {e}")
                return []

    @staticmethod
    async def get_catalog(
        source_id: int | None = None,
        folder: str | None = None,
        series_hash: str | None = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "alpha",
        use_random_covers: bool = True,
    ) -> dict[str, Any]:
        """
        Navega por el catálogo agrupando por series_hash o mostrando volúmenes (Async).
        """
        async with pg_manager.get_session() as session:
            try:
                if series_hash:
                    # List volumes of a specific series
                    stmt = (
                        select(LocalBook)
                        .where(LocalBook.series_hash == series_hash)
                        .order_by(LocalBook.volume.asc())
                    )
                    res = await session.execute(stmt)
                    books = res.scalars().all()
                    items = [b.to_dict() for b in books]
                    return {"items": items, "total": len(items), "type": "volumes"}

                # Root or folder navigation: Use SeriesMetadata
                stmt = select(SeriesMetadata)

                if source_id:
                    stmt = stmt.join(LocalBook).where(LocalBook.source_id == source_id).distinct()

                stmt = stmt.order_by(SeriesMetadata.series_name.asc())

                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_items = (await session.execute(count_stmt)).scalar() or 0

                start = (page - 1) * page_size
                stmt = stmt.offset(start).limit(page_size)

                res = await session.execute(stmt)
                series_list = res.scalars().all()

                items = []
                for s in series_list:
                    items.append(
                        {
                            "id": f"series_{s.series_hash}",
                            "title": s.series_name,
                            "series_spanish": s.series_spanish,
                            "is_folder": True,
                            "numBooks": s.book_count,
                            "book_type": s.book_type,
                            "cover": s.cover_url,
                            "series_hash": s.series_hash,
                        }
                    )

                return {
                    "items": items,
                    "total": total_items,
                    "page": page,
                    "totalPages": (total_items + page_size - 1) // page_size,
                    "type": "series",
                }

            except Exception as e:
                logger.error(f"[LibraryService.get_catalog] Error: {e}")
                return {"items": [], "total": 0}
