from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import os
from PIL import Image

from utils.library_db import get_session, COVERS_DIR, THUMBNAILS_DIR
from models.library_models import LocalBook, LibrarySource
from api.deps import require_mini_app_access, require_admin

router = APIRouter(tags=["library"])


@router.get("/api/library/sources")
async def get_sources(user_data: dict = Depends(require_mini_app_access)):
    """
    Lista todas las fuentes de biblioteca configuradas.
    """
    session = get_session()
    try:
        sources = session.query(LibrarySource).all()
        result = []
        for s in sources:
            # Pick a random book from this source to use as cover
            random_book = (
                session.query(LocalBook)
                .filter(LocalBook.source_id == s.id)
                .order_by(func.random())
                .first()
            )
            result.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "path": s.path,
                    "cover": random_book.cover_path if random_book else None,
                    "lastScanned": (
                        s.last_scanned.isoformat() if s.last_scanned else None
                    ),
                }
            )
        return result
    finally:
        session.close()


@router.get("/api/library/search")
async def search_local_books(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    source_id: Optional[int] = None,
    search_type: str = Query(
        "all", regex="^(all|title|author|illustrator|translator|genres)$"
    ),
    user_data: dict = Depends(require_mini_app_access),
):
    """
    Busca libros en la base de datos local con filtros opcionales usando FTS5.
    """
    session = get_session()
    try:
        from sqlalchemy import text
        import re

        # Limpiar query para FTS5
        clean_q = re.sub(r"[^\w\s]", " ", q).strip()

        if not clean_q:
            # Fallback a LIKE si la query solo tiene símbolos
            query = session.query(LocalBook)
            if source_id:
                query = query.filter(LocalBook.source_id == source_id)
            search_filter = f"%{q}%"
            query = query.filter(LocalBook.title.ilike(search_filter))
            results = query.limit(100).all()
        else:
            # Usar FTS5 MATCH
            if search_type == "all":
                # Búsqueda en todos los campos indexados
                match_expr = "books_fts MATCH :q"
            elif search_type == "title":
                match_expr = "title MATCH :q"
            elif search_type == "author":
                match_expr = "author MATCH :q"
            elif search_type == "illustrator":
                match_expr = "illustrator MATCH :q"
            elif search_type == "translator":
                match_expr = "publisher MATCH :q"
            elif search_type == "genres":
                match_expr = "tags MATCH :q"
            else:
                match_expr = "books_fts MATCH :q"

            sql = text(f"SELECT rowid FROM books_fts WHERE {match_expr} ORDER BY rank")
            matching_ids = session.execute(sql, {"q": f"{clean_q}*"}).scalars().all()

            if not matching_ids:
                return {"items": [], "total": 0, "page": page, "totalPages": 0}

            query = session.query(LocalBook).filter(LocalBook.id.in_(matching_ids))
            if source_id:
                query = query.filter(LocalBook.source_id == source_id)

            # Mantener orden de FTS5 rank
            all_results = query.all()
            id_to_book = {b.id: b for b in all_results}
            results = [id_to_book[id] for id in matching_ids if id in id_to_book][:100]

        response = []
        for book in results:
            d = book.to_dict()
            # Limpiar tags de tipo [NL], [NW], [WN] de cualquier campo de texto
            clean_regex = r"\s*\[(NL|NW|WN)\]\s*"

            if book.series:
                clean_series = re.sub(
                    clean_regex, "", book.series, flags=re.IGNORECASE
                ).strip()
                d["cleanTitle"] = clean_series
                d["englishTitle"] = clean_series
            else:
                clean_title = re.sub(
                    clean_regex, "", book.title, flags=re.IGNORECASE
                ).strip()
                d["cleanTitle"] = clean_title
                d["englishTitle"] = clean_title

            # Asegurar compatibilidad con el frontend
            d["is_series_folder"] = False
            d["bookType"] = book.book_type
            response.append(d)

        # Paginación manual de la respuesta combinada (series + libros)
        total_items = len(response)
        total_pages = (total_items + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_response = response[start:end]

        return {
            "items": paginated_response,
            "total": total_items,
            "page": page,
            "totalPages": total_pages,
        }
    finally:
        session.close()


@router.get("/api/library/books/{book_id}")
async def get_book_detail(
    book_id: str, user_data: dict = Depends(require_mini_app_access)
):
    """
    Retorna el detalle de un libro específico (con o sin prefijo local_).
    """
    session = get_session()
    try:
        clean_id = book_id.replace("local_", "")
        book = session.query(LocalBook).filter(LocalBook.id == int(clean_id)).first()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        d = book.to_dict()
        # Check if user has downloaded this book
        from repositories.download_repository import download_repo
        d["is_downloaded"] = await download_repo.has_user_downloaded(user_data["user_id"], book.title)
        return d
    finally:
        session.close()


@router.get("/api/library/catalog")
async def get_catalog(
    source_id: Optional[int] = Query(None),
    folder: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    use_random_covers: bool = Query(True),
    sort_by: str = Query(
        "alpha",
        regex="^(alpha|alpha_desc|date_added|date_added_desc|date_updated|date_updated_desc|downloads_desc|rating_desc)$",
    ),
    user_data: dict = Depends(require_mini_app_access),
):
    """
    Navega por la librería local simulando carpetas.
    Soporta paginación y ordenamiento (carpetas primero, luego libros).
    """
    session = get_session()
    try:
        if not source_id:
            # Si no hay source_id, listar fuentes como carpetas raíz
            sources = session.query(LibrarySource).all()
            items = []
            for s in sources:
                # Cover for root source (random or first based on setting)
                random_book = (
                    session.query(LocalBook)
                    .filter(LocalBook.source_id == s.id)
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
                        "cover": random_book.cover_path if random_book else None,
                        "numBooks": session.query(LocalBook)
                        .filter(LocalBook.source_id == s.id)
                        .count(),
                    }
                )
            # No paginamos las fuentes (suelen ser pocas)
            return {"items": items, "total": len(items), "page": 1, "totalPages": 1}

        source = (
            session.query(LibrarySource).filter(LibrarySource.id == source_id).first()
        )
        if not source:
            raise HTTPException(status_code=404, detail="Fuente no encontrada")

        # Buscar todos los libros en esta fuente
        books = session.query(LocalBook).filter(LocalBook.source_id == source_id).all()

        books_in_folder = []
        folders_map = {}  # f_name -> representative_book (dict)

        # Sort books by volume/title to get a good representative (like Vol 1)
        sorted_books = sorted(
            books, key=lambda x: (x.series or "", x.volume or 0, x.title.lower())
        )

        base_path = source.path.rstrip("/")
        if folder:
            current_lookup = os.path.join(base_path, folder.strip("/"))
        else:
            current_lookup = base_path

        for b in sorted_books:
            b_dict = b.to_dict()
            rel_path = os.path.relpath(os.path.dirname(b.filepath), current_lookup)

            if rel_path == ".":
                # Libro en la carpeta actual
                books_in_folder.append(b_dict)
            elif not rel_path.startswith(".."):
                # Carpeta hija
                subfolder = rel_path.split(os.sep)[0]
                if subfolder not in folders_map:
                    folders_map[subfolder] = {
                        "representative": b_dict,
                        "all_series": {b.series} if b.series else set(),
                    }
                else:
                    if b.series:
                        folders_map[subfolder]["all_series"].add(b.series)

        # Convertir carpetas a objetos con metadatos de su "representante"
        folders_list = []
        for f_name, meta in sorted(folders_map.items(), key=lambda x: x[0].lower()):
            rep = meta["representative"]
            # Si todos los libros en la carpeta pertenecen a una misma serie, usar el nombre de la serie como título
            display_title = f_name
            if len(meta["all_series"]) == 1:
                series_name = list(meta["all_series"])[0]
                if series_name:
                    display_title = series_name

            # Random cover from books in this subfolder
            current_sub_path = (
                os.path.join(base_path, folder, f_name)
                if folder
                else os.path.join(base_path, f_name)
            )

            # Cover from books in this subfolder (random or first based on setting)
            subfolder_book_query = session.query(LocalBook).filter(
                LocalBook.source_id == source_id,
                LocalBook.filepath.like(f"{current_sub_path}{os.sep}%"),
            )
            random_cover_book = subfolder_book_query.order_by(
                func.random() if use_random_covers else LocalBook.id
            ).first()

            folders_list.append(
                {
                    "id": f"dir_{source_id}_{f_name}",
                    "title": display_title,
                    "is_folder": True,
                    "folder_path": os.path.join(folder, f_name) if folder else f_name,
                    "source_id": source_id,
                    "cover": (
                        random_cover_book.cover_path
                        if random_cover_book
                        else rep.get("cover")
                    ),
                    "author": rep.get("author"),
                    "numBooks": subfolder_book_query.count(),
                    "tags": rep.get("tags"),
                    "series": rep.get("series"),
                    "bookType": (
                        random_cover_book.book_type
                        if random_cover_book
                        else rep.get("book_type")
                    ),
                    # Add date fields for sorting
                    "created_at": (
                        random_cover_book.file_created_at.isoformat()
                        if random_cover_book and random_cover_book.file_created_at
                        else None
                    ),
                    "modified_at": (
                        random_cover_book.file_modified_at.isoformat()
                        if random_cover_book and random_cover_book.file_modified_at
                        else None
                    ),
                }
            )

        # Sort folders based on sort_by parameter
        if sort_by == "alpha":
            folders_list.sort(key=lambda x: x["title"].lower())
        elif sort_by == "alpha_desc":
            folders_list.sort(key=lambda x: x["title"].lower(), reverse=True)
        elif sort_by == "date_added":
            folders_list.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        elif sort_by == "date_added_desc":
            folders_list.sort(key=lambda x: x.get("created_at") or "")
        elif sort_by == "date_updated":
            folders_list.sort(key=lambda x: x.get("modified_at") or "", reverse=True)
        elif sort_by == "date_updated_desc":
            folders_list.sort(key=lambda x: x.get("modified_at") or "")
        elif sort_by == "downloads_desc":
            # Sort by download count using SQL query
            from sqlalchemy import func, select
            from models.download_models import DownloadHistory

            # Get download counts for all books
            download_counts_query = (
                session.query(
                    DownloadHistory.title,
                    func.count(DownloadHistory.id).label("download_count")
                )
                .group_by(DownloadHistory.title)
            )
            download_counts = {row.title: row.download_count for row in download_counts_query.all()}

            # Sort books by download count
            books_in_folder.sort(
                key=lambda x: download_counts.get(x.get("title", ""), 0),
                reverse=True
            )
        elif sort_by == "rating_desc":
            # Sort by rating average, then by rating count
            books_in_folder.sort(key=lambda x: (x.get("rating_average") or 0, x.get("rating_count") or 0), reverse=True)

        # Ordenar libros alfabéticamente solo si no se aplicó otro ordenamiento
        if sort_by not in ("downloads_desc", "rating_desc"):
            books_in_folder.sort(key=lambda x: x["title"].lower())

        # Combinar: Carpetas primero, luego libros
        all_items = folders_list + books_in_folder
        total = len(all_items)

        # Paginación
        start = (page - 1) * page_size
        end = start + page_size
        paged_items = all_items[start:end]

        total_pages = (total + page_size - 1) // page_size

        return {
            "items": paged_items,
            "total": total,
            "page": page,
            "totalPages": total_pages,
            "source_name": source.name if source else None,
        }
    finally:
        session.close()


# Las portadas se servirán vía StaticFiles montado en api/main.py

# ===== BACKUP ENDPOINTS =====
from services.library_backup_service import LibraryBackupService
from utils.library_db import DB_PATH

# Inicializar servicio de backup
backup_service = LibraryBackupService(db_path=DB_PATH)


@router.post("/api/library/backup")
async def create_backup(
    compress: bool = Query(True), user_data: dict = Depends(require_admin)
):
    """
    Crea un backup manual de la base de datos de la biblioteca.
    Solo disponible para administradores.
    """
    try:
        backup_path = backup_service.create_backup(compress=compress)
        return {
            "success": True,
            "message": "Backup creado exitosamente",
            "backup_path": backup_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating backup: {str(e)}")


@router.get("/api/library/backups")
async def list_backups(user_data: dict = Depends(require_admin)):
    """
    Lista todos los backups disponibles.
    Solo disponible para administradores.
    """
    try:
        backups = backup_service.list_backups()
        stats = backup_service.get_backup_stats()
        return {"backups": backups, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing backups: {str(e)}")


@router.post("/api/library/restore")
async def restore_backup(
    backup_filename: str = Query(...), user_data: dict = Depends(require_admin)
):
    """
    Restaura la base de datos desde un backup.
    Solo disponible para administradores.
    """
    try:
        success = backup_service.restore_backup(backup_filename)
        return {"success": success, "message": "Base de datos restaurada exitosamente"}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restoring backup: {str(e)}")


@router.delete("/api/library/backups/{backup_filename}")
async def delete_backup(backup_filename: str, user_data: dict = Depends(require_admin)):
    """
    Elimina un backup específico.
    Solo disponible para administradores.
    """
    try:
        success = backup_service.delete_backup(backup_filename)
        if success:
            return {"success": True, "message": "Backup eliminado exitosamente"}
        else:
            raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting backup: {str(e)}")


# ===== EXPORT/IMPORT ENDPOINTS =====
from services.library_export_service import LibraryExportService
from fastapi.responses import JSONResponse


@router.get("/api/library/export")
async def export_library(
    source_id: Optional[int] = Query(None),
    series: Optional[str] = Query(None),
    user_data: dict = Depends(require_admin),
):
    """
    Exporta metadatos de la biblioteca en formato JSON.
    Solo disponible para administradores.
    """
    try:
        data = LibraryExportService.export_library(source_id=source_id, series=series)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error exporting library: {str(e)}"
        )


@router.post("/api/library/import")
async def import_library(
    data: dict, merge: bool = Query(True), user_data: dict = Depends(require_admin)
):
    """
    Importa metadatos de la biblioteca desde JSON.
    Solo disponible para administradores.
    """
    try:
        stats = LibraryExportService.import_from_json(data, merge=merge)
        return {"success": True, "message": "Importación completada", "stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error importing library: {str(e)}"
        )


# ===== MAINTENANCE ENDPOINTS =====
from services.library_maintenance_service import LibraryMaintenanceService


@router.post("/api/library/optimize")
async def optimize_database(user_data: dict = Depends(require_admin)):
    """
    Optimiza la base de datos (VACUUM y ANALYZE).
    Solo disponible para administradores.
    """
    try:
        result = LibraryMaintenanceService.optimize_database()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error optimizing database: {str(e)}"
        )


@router.post("/api/library/cleanup")
async def cleanup_orphaned_files(user_data: dict = Depends(require_admin)):
    """
    Elimina archivos de portada huérfanos.
    Solo disponible para administradores.
    """
    try:
        result = LibraryMaintenanceService.cleanup_orphaned_covers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error cleaning up files: {str(e)}"
        )


@router.get("/api/library/stats")
async def get_library_statistics(user_data: dict = Depends(require_mini_app_access)):
    """
    Obtiene estadísticas detalladas de la biblioteca.
    """
    try:
        stats = LibraryMaintenanceService.get_library_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting statistics: {str(e)}"
        )


@router.get("/api/library/thumbnail/{filename}")
async def get_thumbnail(filename: str):
    """
    Genera y sirve una miniatura (thumbnail) de la portada solicitada.
    """
    original_path = os.path.join(COVERS_DIR, filename)
    thumb_path = os.path.join(THUMBNAILS_DIR, filename)

    # 1. Si ya existe la miniatura, servirla directamente
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path)

    # 2. Si no existe la original, 404
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404, detail="Original cover not found")

    # 3. Generar miniatura (Lazy Generation)
    try:
        with Image.open(original_path) as img:
            # Dimensiones optimizadas para grid (aprox 180x260 manteniendo aspecto)
            img.thumbnail((200, 300))
            # Guardar como WebP si es posible para mejor compresión, o mantener original
            img.save(thumb_path, optimize=True, quality=80)

        return FileResponse(thumb_path)
    except Exception as e:
        # Fallback a la original si falla la generación
        return FileResponse(original_path)
