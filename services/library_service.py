import logging
import re
from typing import Any

from sqlalchemy import String, cast, func, or_, select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata
from repositories.download_repository import download_repo

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
        """
        async with pg_manager.get_session() as session:
            try:
                pattern = f"%{query}%"
                
                # Filtros base para cualquier tipo de búsqueda
                filters = [
                    LocalBook.title.ilike(pattern),
                    LocalBook.author.ilike(pattern),
                    LocalBook.series.ilike(pattern),
                    LocalBook.series_spanish.ilike(pattern),
                    LocalBook.romaji_title.ilike(pattern),
                    LocalBook.english_title.ilike(pattern)
                ]
                
                # Filtros adicionales basados en el tipo de búsqueda
                if search_type in ("all", "todos", "genres", "géneros", "tags"):
                     filters.append(cast(LocalBook.tags, String).ilike(pattern))
                     
                if search_type in ("all", "todos", "translator", "traductor"):
                     filters.append(LocalBook.translator.ilike(pattern))

                if search_type in ("all", "todos", "illustrator", "ilustrador"):
                     filters.append(LocalBook.illustrator.ilike(pattern))

                if search_type in ("all", "todos", "layout", "maquetador"):
                    filters.append(LocalBook.layout_by.ilike(pattern))

                stmt = select(LocalBook).where(or_(*filters))
                
                if source_id:
                    stmt = stmt.where(LocalBook.source_id == source_id)
                
                # Count total
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_items = (await session.execute(count_stmt)).scalar() or 0
                
                # Paginación y ejecución
                start = (page - 1) * items_per_page
                stmt = stmt.order_by(LocalBook.title.asc()).offset(start).limit(items_per_page)
                result = await session.execute(stmt)
                books = result.scalars().all()

                results = []
                for b in books:
                    d = b.to_dict()
                    d["is_folder"] = False
                    d["download_count"] = await download_repo.get_total_download_count(
                        b.title, book_hash=b.book_hash
                    )
                    # Cleaning for legacy compatibility
                    d["cleanTitle"] = (
                        b.english_title
                        or b.series
                        or re.sub(r"\s*\[.*?\]\s*", " ", b.title).strip()
                    )
                    d["book_hash"] = b.book_hash
                    results.append(d)

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
        sort_by: str = "a-z"
    ) -> dict[str, Any]:
        """
        Búsqueda agrupada por series_hash. Retorna un objeto similar a Series
        en lugar de volúmenes individuales (Exclusivo para PostgreSQL).
        """
        async with pg_manager.get_session() as session:
            try:
                pattern = f"%{query}%"
                
                # Búsqueda directa en SeriesMetadata - Mucho más eficiente
                stmt = select(SeriesMetadata).where(
                    or_(
                        SeriesMetadata.series_name.ilike(pattern),
                        SeriesMetadata.series_spanish.ilike(pattern),
                        SeriesMetadata.author.ilike(pattern),
                        cast(SeriesMetadata.tags, String).ilike(pattern)
                    )
                )

                if source_id:
                    # Si filtramos por origen, debemos unir con LocalBook
                    stmt = stmt.join(LocalBook).where(LocalBook.source_id == source_id).distinct()

                # Order by logic
                if sort_by == "newest":
                    stmt = stmt.order_by(SeriesMetadata.id.desc())
                elif sort_by == "popular":
                    stmt = stmt.order_by(SeriesMetadata.rating_count.desc())
                else: # a-z default
                    stmt = stmt.order_by(SeriesMetadata.series_name.asc())

                # Count total series
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_series = (await session.execute(count_stmt)).scalar() or 0

                # Pagination
                start = (page - 1) * items_per_page
                stmt = stmt.offset(start).limit(items_per_page)
                
                res = await session.execute(stmt)
                series_list = res.scalars().all()

                results = []
                for s in series_list:
                    results.append({
                        "id": f"series_{s.series_hash}",
                        "series_hash": s.series_hash,
                        "title": s.series_name,
                        "series_spanish": s.series_spanish,
                        "series": s.series_name,
                        "author": s.author,
                        "description": s.description,
                        "cover": s.cover_url, # Default (low)
                        "coverUrl": {
                            "cover_low": s.cover_url,
                            "cover_medium": s.cover_url.replace("_low.jpg", "_medium.jpg") if s.cover_url else None,
                            "cover_high": s.cover_url.replace("_low.jpg", "_high.jpg") if s.cover_url else None,
                            "cover_original": s.cover_url.replace("_low.jpg", "_original.jpg") if s.cover_url else None,
                            "cover": s.cover_url
                        },
                        "numBooks": s.book_count,
                        "rating_average": s.rating_average,
                        "rating_count": s.rating_count,
                        "is_series": True,
                        "type": "series"
                    })

                return {
                    "results": results,
                    "currentPage": page,
                    "totalPages": (total_series + items_per_page - 1) // items_per_page,
                    "totalItems": total_series
                }

            except Exception as e:
                logger.error(f"[LibraryService.search_series] Error: {e}")
                return {"results": [], "totalItems": 0}

    @staticmethod
    async def get_series_volumes(series_hash: str, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
        """Retorna los volúmenes de una serie agrupada con soporte para paginación (Async)."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(LocalBook).where(LocalBook.series_hash == series_hash).order_by(LocalBook.volume.asc())
                if limit:
                    stmt = stmt.offset(offset).limit(limit)
                res = await session.execute(stmt)
                books = res.scalars().all()
                
                results = []
                for b in books:
                    d = b.to_dict()
                    d["download_count"] = await download_repo.get_total_download_count(
                        b.title, b.book_hash
                    )
                    # Use actual column values from LocalBook (synchronized with RatingService)
                    d["rating_average"] = b.rating_average or 0.0
                    d["rating_count"] = b.rating_count or 0
                    results.append(d)
                
                return results
            except Exception as e:
                logger.error(f"[LibraryService.get_series_volumes] Error: {e}")
                return []

    @staticmethod
    async def get_book_by_id(book_id: int) -> dict[str, Any] | None:
        """Busca un libro por su ID en la base de datos local (Async)."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(LocalBook).where(LocalBook.id == book_id)
                res = await session.execute(stmt)
                book = res.scalar_one_or_none()
                if not book:
                    return None
                d = book.to_dict()

                d["download_count"] = await download_repo.get_total_download_count(
                    book.title, book_hash=book.book_hash
                )
                # Ensure cleanTitle and book_hash are present for frontend/hashing consistency
                d["cleanTitle"] = (
                    book.english_title
                    or book.series
                    or re.sub(r"\s*\[.*?\]\s*", " ", book.title).strip()
                )
                d["book_hash"] = book.book_hash
                return d
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
                    series=series_name,
                    author=book.author,
                    book_type=book.book_type
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
                stmt = select(LocalBook).where(
                    or_(LocalBook.series.is_(None), LocalBook.series == "")
                ).order_by(LocalBook.author, LocalBook.title)
                
                result = await session.execute(stmt)
                books = result.scalars().all()
                
                # 2. Agrupamiento lógico simple en memoria (Python)
                # Postgres tiene extensiones como pg_trgm para similitud, pero para simplificar
                # y no depender de extensiones, hacemos un chequeo básico aquí.
                from difflib import SequenceMatcher
                
                groups = []
                used_ids = set()

                for i, book_a in enumerate(books):
                    if book_a.id in used_ids:
                        continue
                        
                    current_group = [book_a]
                    used_ids.add(book_a.id)
                    
                    for _j, book_b in enumerate(books[i+1:], start=i+1):
                        if book_b.id in used_ids:
                            continue
                            
                        # Mismo autor es un requisito fuerte
                        if book_a.author and book_b.author and book_a.author.lower() != book_b.author.lower():
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
                        match = SequenceMatcher(None, current_group[0].title, current_group[1].title).find_longest_match(0, len(current_group[0].title), 0, len(current_group[1].title))
                        suggested_name = current_group[0].title[match.a: match.a + match.size].strip(" -:volume")

                        groups.append({
                            "suggested_series": suggested_name or common_title,
                            "confidence": "high",
                            "books": [b.to_dict() for b in current_group]
                        })

                return groups
            except Exception as e:
                logger.error(f"[LibraryService.get_regroup_suggestions] Error: {e}")
                return []

    @staticmethod
    async def get_books_without_series(limit: int = 100) -> list[dict[str, Any]]:
        """Retorna una lista simple de libros que no tienen serie asignada."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(LocalBook)\
                    .where(or_(LocalBook.series.is_(None), LocalBook.series == ""))\
                    .order_by(LocalBook.indexed_at.desc())\
                    .limit(limit)
                
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
                    stmt = select(LocalBook).where(LocalBook.series_hash == series_hash).order_by(LocalBook.volume.asc())
                    res = await session.execute(stmt)
                    books = res.scalars().all()
                    items = [b.to_dict() for b in books]
                    return {
                        "items": items,
                        "total": len(items),
                        "type": "volumes"
                    }

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
                    items.append({
                        "id": f"series_{s.series_hash}",
                        "title": s.series_name,
                        "series_spanish": s.series_spanish,
                        "is_folder": True,
                        "numBooks": s.book_count,
                        "cover": s.cover_url,
                        "series_hash": s.series_hash
                    })

                return {
                    "items": items,
                    "total": total_items,
                    "page": page,
                    "totalPages": (total_items + page_size - 1) // page_size,
                    "type": "series"
                }

            except Exception as e:
                logger.error(f"[LibraryService.get_catalog] Error: {e}")
                return {"items": [], "total": 0}
