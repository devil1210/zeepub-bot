import logging
import re
import os
from typing import List, Dict, Any, Optional
from sqlalchemy import text, func
from utils.library_db import get_session
from models.library_models import LocalBook, LibrarySource

logger = logging.getLogger(__name__)


class LibraryService:
    @staticmethod
    async def search_books(
        query: str, 
        page: int = 1, 
        items_per_page: int = 10,
        search_type: str = "all",
        source_id: Optional[int] = None
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
                if search_type == "all":
                    match_expr = "books_fts MATCH :q"
                elif search_type == "title":
                    match_expr = "title MATCH :q"
                elif search_type == "author":
                    match_expr = "author MATCH :q"
                elif search_type in ("illustrator", "translator", "genres"):
                    field_map = {"illustrator": "illustrator", "translator": "translator", "genres": "tags"}
                    match_expr = f"{field_map[search_type]} MATCH :q"
                else:
                    match_expr = "books_fts MATCH :q"

                sql = text(f"SELECT rowid FROM books_fts WHERE {match_expr} ORDER BY rank")
                params = {"q": f"{clean_q}*"}

                matching_ids = session.execute(sql, params).scalars().all()

                if not matching_ids:
                    return {"results": [], "currentPage": page, "totalPages": 0, "totalItems": 0, "items": []}

                books_query = session.query(LocalBook).filter(LocalBook.id.in_(matching_ids))
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

            from models.download_models import DownloadHistory
            dl_counts = {r.title: r.c for r in session.query(DownloadHistory.title, func.count(DownloadHistory.id).label("c")).group_by(DownloadHistory.title).all()}

            results = []
            for b in paginated_books:
                d = b.to_dict()
                d["is_folder"] = False
                d["download_count"] = dl_counts.get(b.title, 0)
                # Cleaning for legacy compatibility
                d["cleanTitle"] = b.series_clean or re.sub(r"\s*\[.*?\]\s*", " ", b.series or b.title).strip()
                results.append(d)

            total_pages = (total_items + items_per_page - 1) // items_per_page

            return {
                "results": results,      # Mini App format
                "items": results,        # Library API format
                "currentPage": page,
                "page": page,            # Library API alias
                "totalPages": total_pages,
                "totalItems": total_items,
                "total": total_items     # Library API alias
            }
        except Exception as e:
            logger.error(f"[LibraryService.search_books] Error: {e}")
            return {"results": [], "items": [], "currentPage": page, "page": page, "totalPages": 0, "totalItems": 0, "total": 0}
        finally:
            session.close()

    @staticmethod
    async def get_book_by_id(book_id: int) -> Optional[Dict[str, Any]]:
        """Busca un libro por su ID en la base de datos local."""
        session = get_session()
        try:
            from models.download_models import DownloadHistory
            book = session.query(LocalBook).filter_by(id=book_id).first()
            if not book: return None
            d = book.to_dict()
            d["download_count"] = session.query(func.count(DownloadHistory.id)).filter_by(title=book.title).scalar() or 0
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
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "alpha",
        use_random_covers: bool = True
    ) -> Dict[str, Any]:
        """
        Lógica para navegar por el catálogo local simulando carpetas.
        """
        session = get_session()
        try:
            from models.download_models import DownloadHistory
            dl_counts = {r.title: r.c for r in session.query(DownloadHistory.title, func.count(DownloadHistory.id).label("c")).group_by(DownloadHistory.title).all()}

            if not source_id:
                sources = session.query(LibrarySource).all()
                items = []
                for s in sources:
                    random_book = session.query(LocalBook).filter_by(source_id=s.id).order_by(func.random() if use_random_covers else LocalBook.id).first()
                    items.append({
                        "id": f"source_{s.id}",
                        "title": s.name,
                        "is_folder": True,
                        "folder_path": "",
                        "source_id": s.id,
                        "cover": random_book.cover_path if random_book else None,
                        "numBooks": session.query(LocalBook).filter_by(source_id=s.id).count(),
                    })
                return {"items": items, "total": len(items), "page": 1, "totalPages": 1}

            source = session.query(LibrarySource).filter_by(id=source_id).first()
            if not source:
                return {"items": [], "total": 0, "page": page, "totalPages": 0}

            books = session.query(LocalBook).filter_by(source_id=source_id).all()
            books_in_folder = []
            folders_map = {}  # subfolder -> {rep, all_series}

            base_path = source.path.rstrip("/")
            current_lookup = os.path.join(base_path, folder.strip("/")) if folder else base_path

            for b in books:
                rel_path = os.path.relpath(os.path.dirname(b.filepath), current_lookup)
                if rel_path == ".":
                    d = b.to_dict()
                    d["download_count"] = dl_counts.get(b.title, 0)
                    books_in_folder.append(d)
                elif not rel_path.startswith(".."):
                    sub = rel_path.split(os.sep)[0]
                    if sub not in folders_map:
                        folders_map[sub] = {"rep": b, "all_series": {b.series} if b.series else set()}
                    else:
                        if b.series: folders_map[sub]["all_series"].add(b.series)

            folders_list = []
            for f_name, meta in folders_map.items():
                rep = meta["rep"]
                display_title = f_name
                if len(meta["all_series"]) == 1:
                    s_name = list(meta["all_series"])[0]
                    if s_name:
                        display_title = rep.series_clean or s_name

                sub_path = os.path.join(base_path, folder, f_name) if folder else os.path.join(base_path, f_name)
                sub_query = session.query(LocalBook).filter(LocalBook.source_id == source_id, LocalBook.filepath.like(f"{sub_path}{os.sep}%"))
                rnd_book = sub_query.order_by(func.random() if use_random_covers else LocalBook.id).first()

                folders_list.append({
                    "id": f"dir_{source_id}_{f_name}",
                    "title": display_title,
                    "is_folder": True,
                    "folder_path": os.path.join(folder, f_name) if folder else f_name,
                    "source_id": source_id,
                    "cover": rnd_book.cover_path if rnd_book else rep.cover_path,
                    "author": rep.author,
                    "numBooks": sub_query.count(),
                    "series": rep.series,
                    "series_clean": rep.series_clean,
                    "tags": rep.tags,
                    "demographics": rep.demographics,
                    "book_type": rep.book_type,
                    "created_at": rnd_book.file_created_at.isoformat() if rnd_book and rnd_book.file_created_at else None,
                    "modified_at": rnd_book.file_modified_at.isoformat() if rnd_book and rnd_book.file_modified_at else None,
                })

            # Sorting
            if sort_by == "alpha":
                folders_list.sort(key=lambda x: x["title"].lower())
                books_in_folder.sort(key=lambda x: x["title"].lower())
            elif sort_by == "alpha_desc":
                folders_list.sort(key=lambda x: x["title"].lower(), reverse=True)
                books_in_folder.sort(key=lambda x: x["title"].lower(), reverse=True)
            elif "date_added" in sort_by:
                rev = "desc" not in sort_by
                folders_list.sort(key=lambda x: x.get("created_at") or "", reverse=rev)
                books_in_folder.sort(key=lambda x: x.get("file_created_at") or "", reverse=rev)
            elif "date_updated" in sort_by:
                rev = "desc" not in sort_by
                folders_list.sort(key=lambda x: x.get("modified_at") or "", reverse=rev)
                books_in_folder.sort(key=lambda x: x.get("file_modified_at") or "", reverse=rev)
            elif sort_by == "downloads_desc":
                from models.download_models import DownloadHistory
                dl_counts = {r.title: r.c for r in session.query(DownloadHistory.title, func.count(DownloadHistory.id).label("c")).group_by(DownloadHistory.title).all()}
                folders_list.sort(key=lambda x: dl_counts.get(x["title"], 0), reverse=True)
                books_in_folder.sort(key=lambda x: dl_counts.get(x["title"], 0), reverse=True)

            all_items = folders_list + books_in_folder
            start = (page - 1) * page_size
            end = start + page_size

            return {
                "items": all_items[start:end],
                "total": len(all_items),
                "page": page,
                "totalPages": (len(all_items) + page_size - 1) // page_size,
                "source_name": source.name
            }
        finally:
            session.close()
