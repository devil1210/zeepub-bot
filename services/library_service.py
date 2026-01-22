import logging
import re
from typing import Dict, Any, Optional
from sqlalchemy import text, func, String
from utils.library_db import get_session
from models.library_models import LocalBook, LibrarySource

logger = logging.getLogger(__name__)


def _get_download_counts_from_zeepub_db() -> Dict[str, int]:
    """Helper function to get download counts from zeepub.db"""
    import sqlite3
    from config.config_settings import config
    from utils.epub_extractor import clean_metadata_tags

    dl_counts = {}
    try:
        conn = sqlite3.connect(config.URL_CACHE_DB_PATH)
        # Fetch both title and clean_title
        cursor = conn.execute(
            "SELECT title, clean_title, COUNT(*) as c FROM download_history GROUP BY title, clean_title"
        )
        for row in cursor.fetchall():
            dirty_title, clean_title_db, count = row
            # If clean_title is already in DB use it, else clean the dirty title
            key = clean_title_db or clean_metadata_tags(dirty_title)
            dl_counts[key] = dl_counts.get(key, 0) + count
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching download counts from zeepub.db: {e}")
    return dl_counts


class LibraryService:
    @staticmethod
    async def search_books(
        query: str,
        page: int = 1,
        items_per_page: int = 10,
        search_type: str = "all",
        source_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Realiza una búsqueda de libros utilizando FTS5 si está disponible,
        o fallback a ILIKE.
        """
        session = get_session()
        try:
            # Limpiar query para FTS
            clean_q = re.sub(r"[^\w\s]", " ", query).strip()

            if not clean_q:
                # Fallback simple
                books_query = session.query(LocalBook).filter(
                    LocalBook.title.ilike(f"%{query}%")
                )
                if source_id:
                    books_query = books_query.filter(LocalBook.source_id == source_id)

                total_items = books_query.count()
                books = books_query.limit(100).all()
            else:
                # Búsqueda FTS5
                if search_type == "all" or search_type == "todos":
                    match_expr = "books_fts MATCH :q"
                elif search_type == "title" or search_type == "título":
                    match_expr = "title MATCH :q"
                elif search_type == "author" or search_type == "autor":
                    match_expr = "author MATCH :q"
                elif search_type == "serie":
                    match_expr = "series MATCH :q"
                elif search_type in ("illustrator", "ilustrador", "translator", "traductor", "genres", "géneros", "layout", "maquetador"):
                    field_map = {
                        "illustrator": "illustrator",
                        "ilustrador": "illustrator",
                        "translator": "translator",
                        "traductor": "translator",
                        "genres": "tags",
                        "géneros": "tags",
                        "layout": "layout_by",
                        "maquetador": "layout_by",
                    }
                    match_expr = f"{field_map[search_type]} MATCH :q"
                else:
                    match_expr = "books_fts MATCH :q"

                sql = text(
                    f"SELECT rowid FROM books_fts WHERE {match_expr} ORDER BY rank"
                )
                params = {"q": f"{clean_q}*"}

                matching_ids = session.execute(sql, params).scalars().all()

                if not matching_ids:
                    return {
                        "results": [],
                        "currentPage": page,
                        "totalPages": 0,
                        "totalItems": 0,
                        "items": [],
                    }

                books_query = session.query(LocalBook).filter(
                    LocalBook.id.in_(matching_ids)
                )
                if source_id:
                    books_query = books_query.filter(LocalBook.source_id == source_id)

                books = books_query.all()
                # Mantener orden de rank
                id_to_book = {b.id: b for b in books}
                books = [id_to_book[bid] for bid in matching_ids if bid in id_to_book]
                total_items = len(books)

            # Paginación
            start = (page - 1) * items_per_page
            end = start + items_per_page
            paginated_books = books[start:end]

            # Results Enrichment
            from repositories.download_repository import download_repo

            results = []
            for b in paginated_books:
                d = b.to_dict()
                d["is_folder"] = False
                d["download_count"] = await download_repo.get_total_download_count(
                    b.title, book_hash=b.content_hash
                )
                # Cleaning for legacy compatibility
                d["cleanTitle"] = (
                    b.english_title
                    or re.sub(r"\s*\[.*?\]\s*", " ", b.series or b.title).strip()
                )
                results.append(d)

            total_pages = (total_items + items_per_page - 1) // items_per_page

            return {
                "results": results,  # Mini App format
                "items": results,  # Library API format
                "currentPage": page,
                "page": page,  # Library API alias
                "totalPages": total_pages,
                "totalItems": total_items,
                "total": total_items,  # Library API alias
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
        finally:
            session.close()

    @staticmethod
    async def search_series(
        query: str,
        page: int = 1,
        items_per_page: int = 20,
        source_id: Optional[int] = None,
        search_type: str = "todos",
        sort_by: str = "a-z"
    ) -> Dict[str, Any]:
        """
        Búsqueda agrupada por series_hash. Retorna un objeto similar a Series
        en lugar de volúmenes individuales.
        """
        session = get_session()
        from repositories.metrics_repository import metrics_repo
        try:
            # Query base: Agrupar por series_hash
            group_query = session.query(
                LocalBook.series_hash,
                func.min(LocalBook.id).label("rep_id"),
                func.count(LocalBook.id).label("num_volumenes"),
                func.avg(func.nullif(LocalBook.rating_average, 0.0)).label("avg_rating"),
                func.sum(LocalBook.rating_count).label("total_votes"),
            )

            if source_id:
                group_query = group_query.filter(LocalBook.source_id == source_id)

            if query:
                # Normalizar search_type (el frontend envía 'todos', 'título', etc)
                s_type = search_type.lower()
                
                if s_type == "título":
                    group_query = group_query.filter(
                        (LocalBook.title.ilike(f"%{query}%"))
                    )
                elif s_type == "serie":
                    group_query = group_query.filter(
                        (LocalBook.series.ilike(f"%{query}%")) |
                        (LocalBook.english_title.ilike(f"%{query}%")) |
                        (LocalBook.spanish_title.ilike(f"%{query}%"))
                    )
                elif s_type == "autor":
                    group_query = group_query.filter(LocalBook.author.ilike(f"%{query}%"))
                elif s_type == "ilustrador":
                    group_query = group_query.filter(LocalBook.illustrator.ilike(f"%{query}%"))
                elif s_type == "traductor":
                    group_query = group_query.filter(LocalBook.translator.ilike(f"%{query}%"))
                elif s_type in ("maquetador", "layout"):
                    group_query = group_query.filter(LocalBook.layout_by.ilike(f"%{query}%"))
                elif s_type in ("grupo", "publisher", "editorial"):
                    group_query = group_query.filter(LocalBook.publisher.ilike(f"%{query}%"))
                elif s_type in ("géneros", "genres", "categoria"):
                    # tags es una columna JSON en PostgreSQL, usar operadores JSON
                    group_query = group_query.filter(
                        (LocalBook.tags.astext.ilike(f"%{query}%")) |
                        (LocalBook.book_type.ilike(f"%{query}%"))
                    )
                else: # todos o fallback
                    group_query = group_query.filter(
                        (LocalBook.title.ilike(f"%{query}%")) | 
                        (LocalBook.series.ilike(f"%{query}%")) |
                        (LocalBook.english_title.ilike(f"%{query}%")) |
                        (LocalBook.spanish_title.ilike(f"%{query}%")) |
                        (LocalBook.romaji_title.ilike(f"%{query}%")) |
                        (LocalBook.jap_title.ilike(f"%{query}%")) |
                        (LocalBook.author.ilike(f"%{query}%")) |
                        (LocalBook.illustrator.ilike(f"%{query}%")) |
                        (LocalBook.translator.ilike(f"%{query}%")) |
                        (LocalBook.layout_by.ilike(f"%{query}%")) |
                        (LocalBook.publisher.ilike(f"%{query}%")) |
                        (LocalBook.isbn.ilike(f"%{query}%")) |
                        (LocalBook.asin.ilike(f"%{query}%")) |
                        (LocalBook.tags.astext.ilike(f"%{query}%")) |
                        (LocalBook.book_type.ilike(f"%{query}%"))
                    )

            group_query = group_query.group_by(LocalBook.series_hash)
            
            # Aplicar ordenamiento global
            # Usamos COALESCE para ordenar por el mismo campo que se muestra en el frontend
            title_expr = func.coalesce(LocalBook.english_title, LocalBook.series, LocalBook.title)
            
            if sort_by == 'a-z':
                group_query = group_query.order_by(func.min(title_expr).asc())
            elif sort_by == 'z-a':
                group_query = group_query.order_by(func.min(title_expr).desc())
            elif sort_by == 'rating':
                group_query = group_query.order_by(func.avg(func.nullif(LocalBook.rating_average, 0.0)).desc())
            elif sort_by in ('added', 'updated'):
                # Priorizar fecha de modificación OPF para ordenamiento cronológico de serie
                group_query = group_query.order_by(func.max(func.coalesce(LocalBook.modified_at_opf, func.cast(LocalBook.file_created_at, String))).desc())
            else:
                group_query = group_query.order_by(func.min(title_expr).asc())
            
            # Paginación sobre los grupos
            total_items = group_query.count()
            groups = group_query.offset((page - 1) * items_per_page).limit(items_per_page).all()

            results = []
            for s_hash, rep_id, num_vols, rating, votes in groups:
                rep = session.query(LocalBook).get(rep_id)
                if not rep: continue
                
                total_downloads = await metrics_repo.get_series_downloads(s_hash)
                
                results.append({
                    "id": f"series_{s_hash}",
                    "series_hash": s_hash,
                    "title": rep.series or rep.english_title or rep.title,
                    "clean_title": rep.series or rep.english_title or rep.title,
                    "englishTitle": rep.english_title,
                    "spanishTitle": rep.spanish_title,
                    "author": rep.author,
                    "illustrator": rep.illustrator,
                    "translator": rep.translator,
                    "typesetter": rep.layout_by,
                    "group": rep.publisher,
                    "cover": rep.cover_low or rep.cover_medium or rep.cover_high or rep.cover_original,
                    "cover_thumb": rep.cover_low,
                    "cover_low": rep.cover_low,
                    "cover_medium": rep.cover_medium,
                    "cover_high": rep.cover_high,
                    "cover_original": rep.cover_original,
                    "summary": rep.description,
                    "categories": rep.tags,
                    "fileType": rep.book_type or "EPUB",
                    "rating_average": round(float(rating or 0), 1),
                    "rating_count": int(votes or 0),
                    "download_count": total_downloads,
                    "numBooks": num_vols,
                    "updatedDate": rep.modified_at_opf or (rep.file_modified_at.isoformat() if rep.file_modified_at else None),
                    "is_series": True,
                    "is_folder": True
                })

            return {
                "results": results,
                "currentPage": page,
                "totalPages": (total_items + items_per_page - 1) // items_per_page,
                "totalResults": total_items
            }
        except Exception as e:
            logger.error(f"[LibraryService.search_series] Error: {e}")
            return {"results": [], "currentPage": page, "totalPages": 0, "totalResults": 0}
        finally:
            session.close()

    @staticmethod
    async def get_series_volumes(series_hash: str) -> list:
        """Retorna todos los volúmenes de una serie agrupada."""
        session = get_session()
        from repositories.metrics_repository import metrics_repo
        try:
            books = session.query(LocalBook).filter_by(series_hash=series_hash).order_by(LocalBook.volume.asc()).all()
            results = []
            for b in books:
                d = b.to_dict()
                d["download_count"] = await metrics_repo.get_total_downloads(b.content_hash)
                results.append(d)
            return results
        except Exception as e:
            logger.error(f"Error get_series_volumes: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    async def get_book_by_id(book_id: int) -> Optional[Dict[str, Any]]:
        """Busca un libro por su ID en la base de datos local."""
        session = get_session()
        try:
            book = session.query(LocalBook).filter_by(id=book_id).first()
            if not book:
                return None
            d = book.to_dict()

            from repositories.download_repository import download_repo

            d["download_count"] = await download_repo.get_total_download_count(
                book.title, book_hash=book.content_hash
            )
            return d
        except Exception as e:
            logger.error(f"[LibraryService.get_book_by_id] Error: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    async def get_catalog(
        source_id: Optional[int] = None,
        folder: Optional[str] = None,
        series_hash: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "alpha",
        use_random_covers: bool = True,
    ) -> Dict[str, Any]:
        """
        Navega por el catálogo agrupando por series_hash o mostrando volúmenes.
        """
        session = get_session()
        from repositories.metrics_repository import metrics_repo

        try:
            # 1. Listar Fuentes (Raíz)
            if not source_id:
                sources = session.query(LibrarySource).all()
                items = []
                for s in sources:
                    # Get metrics for the source
                    source_metrics = (
                        session.query(
                            func.count(LocalBook.series_hash.distinct()).label(
                                "num_series"
                            ),
                            func.avg(func.nullif(LocalBook.rating_average, 0.0)).label(
                                "avg_rating"
                            ),
                            func.sum(LocalBook.rating_count).label("total_votes"),
                        )
                        .filter(LocalBook.source_id == s.id)
                        .first()
                    )

                    # Get total downloads for the source by collecting all series hashes
                    series_hashes = [
                        r[0]
                        for r in session.query(LocalBook.series_hash)
                        .filter_by(source_id=s.id)
                        .distinct()
                        .all()
                    ]
                    source_downloads = await metrics_repo.get_total_downloads_by_hashes(
                        series_hashes
                    )

                    # Get a representative book for the source cover
                    random_book = (
                        session.query(LocalBook)
                        .filter_by(source_id=s.id)
                        .order_by(func.random() if use_random_covers else LocalBook.id)
                        .first()
                    )

                    items.append(
                        {
                            "id": f"source_{s.id}",
                            "title": s.name,
                            "is_folder": True,
                            "folder_path": "",
                            "source_id": s.id,
                            "cover": (random_book.cover_low or random_book.cover_medium) if random_book else None,
                            "cover_thumb": random_book.cover_low if random_book else None,
                            "numBooks": source_metrics.num_series or 0,
                            "rating_average": round(
                                float(source_metrics.avg_rating or 0), 1
                            ),
                            "rating_count": int(source_metrics.total_votes or 0),
                            "download_count": source_downloads,
                        }
                    )
                return {"items": items, "total": len(items), "page": 1, "totalPages": 1}

            source = session.query(LibrarySource).filter_by(id=source_id).first()
            if not source:
                return {"items": [], "total": 0, "page": page, "totalPages": 0}

            # 2. Listar Volúmenes de una Serie (Drill-down)
            if series_hash:
                books_query = session.query(LocalBook).filter_by(
                    source_id=source_id, series_hash=series_hash
                )
                total_items = books_query.count()

                # Sorting para volúmenes
                if sort_by == "alpha":
                    books_query = books_query.order_by(LocalBook.title.asc())
                elif sort_by == "alpha_desc":
                    books_query = books_query.order_by(LocalBook.title.desc())
                elif "date" in sort_by:
                    order = (
                        LocalBook.file_created_at.desc()
                        if "desc" in sort_by
                        else LocalBook.file_created_at.asc()
                    )
                    books_query = books_query.order_by(order)

                books = (
                    books_query.offset((page - 1) * page_size).limit(page_size).all()
                )

                results = []
                from repositories.metrics_repository import metrics_repo

                for b in books:
                    d = b.to_dict()
                    d["is_folder"] = False
                    d["download_count"] = (
                        await metrics_repo.get_total_downloads(b.content_hash)
                        if b.content_hash
                        else 0
                    )
                    results.append(d)

                return {
                    "items": results,
                    "total": total_items,
                    "page": page,
                    "totalPages": (total_items + page_size - 1) // page_size,
                    "source_name": source.name,
                }

            # 3. Listar Series Agrupadas (Vista por defecto del source)
            # Agrupar por series_hash y obtener métricas
            group_query = (
                session.query(
                    LocalBook.series_hash,
                    func.min(LocalBook.id).label("rep_id"),
                    func.count(LocalBook.id).label("num_volumenes"),
                    func.avg(func.nullif(LocalBook.rating_average, 0.0)).label(
                        "avg_rating"
                    ),
                    func.sum(LocalBook.rating_count).label("total_votes"),
                )
                .filter(LocalBook.source_id == source_id)
                .group_by(LocalBook.series_hash)
            )

            all_series_meta = group_query.all()

            # Obtener detalles de los representantes de cada serie
            items = []

            for s_hash, rep_id, num_vols, rating, votes in all_series_meta:
                rep = session.query(LocalBook).get(rep_id)
                if not rep:
                    continue

                # Get series-level downloads from centralized metrics DB
                total_downloads = await metrics_repo.get_series_downloads(s_hash)

                items.append(
                    {
                        "id": f"series_{s_hash}",
                        "title": rep.english_title or rep.series or rep.title,
                        "englishTitle": rep.english_title,
                        "spanishTitle": rep.spanish_title,
                        "is_folder": True,
                        "series_hash": s_hash,
                        "source_id": source_id,
                        "cover": rep.cover_low or rep.cover_medium or rep.cover_high,
                        "cover_thumb": rep.cover_low,
                        "author": rep.author,
                        "numBooks": num_vols,
                        "series": rep.series,
                        "englishTitle": rep.english_title,
                        "spanishTitle": rep.spanish_title,
                        "tags": rep.tags,
                        "demographics": rep.demographics,
                        "book_type": rep.book_type,
                        "rating_average": round(float(rating or 0), 1),
                        "rating_count": int(votes or 0),
                        "download_count": total_downloads,
                        "created_at": (
                            rep.file_created_at.isoformat()
                            if rep.file_created_at
                            else None
                        ),
                        "modified_at": (
                            rep.file_modified_at.isoformat()
                            if rep.file_modified_at
                            else None
                        ),
                    }
                )

            # Sorting para series
            if sort_by == "alpha":
                items.sort(key=lambda x: x["title"].lower())
            elif sort_by == "alpha_desc":
                items.sort(key=lambda x: x["title"].lower(), reverse=True)
            elif "downloads" in sort_by:
                items.sort(key=lambda x: x["download_count"], reverse=True)
            elif "rating" in sort_by:
                items.sort(key=lambda x: x["rating_average"], reverse=True)
            elif "date" in sort_by:
                rev = "desc" in sort_by
                items.sort(key=lambda x: x.get("created_at") or "", reverse=rev)

            start = (page - 1) * page_size
            end = start + page_size

            return {
                "items": items[start:end],
                "total": len(items),
                "page": page,
                "totalPages": (len(items) + page_size - 1) // page_size,
                "source_name": source.name,
            }
        finally:
            session.close()
