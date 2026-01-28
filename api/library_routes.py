import os
import shutil
from typing import Any

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import select

from api.deps import require_admin, require_mini_app_access
from core.db_manager_pg import pg_manager
from models.library_models import LibrarySource
from services.library_service import LibraryService
from services.scanner_service import ScannerService
from utils.library_db import COVERS_DIR, THUMBNAILS_DIR

router = APIRouter(tags=["library"])


@router.get("/api/library/sources")
async def get_sources(user_data: dict = Depends(require_mini_app_access)):
    """Lista todas las fuentes de biblioteca configuradas."""
    return await LibraryService.get_catalog(source_id=None)


@router.get("/api/library/search")
async def search_local_books(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    source_id: int | None = None,
    search_type: str = Query("all", pattern="^(all|title|author|illustrator|translator|genres)$"),
    user_data: dict = Depends(require_mini_app_access),
):
    """Busca libros en la base de datos local con filtros opcionales."""
    return await LibraryService.search_books(
        query=q, page=page, items_per_page=page_size, search_type=search_type, source_id=source_id
    )


@router.post("/api/library/upload")
async def upload_epubs(
    files: list[UploadFile] = File(...),
    source_id: int | None = Query(None),
    user_data: dict = Depends(require_admin),
):
    """
    Sube múltiples archivos EPUB y los escanea inmediatamente.
    """
    valid_files = [f for f in files if f.filename.lower().endswith(".epub")]
    if not valid_files:
        raise HTTPException(status_code=400, detail="No se recibieron archivos EPUB válidos")

    saved_paths = []

    async with pg_manager.get_session() as session:
        # 1. Determinar Source
        stmt = select(LibrarySource)
        if source_id:
            stmt = stmt.where(LibrarySource.id == source_id)
        else:
            stmt = stmt.limit(1)

        result = await session.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            raise HTTPException(status_code=404, detail="No hay fuentes de librería configuradas")

        target_dir = source.path
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"No se pudo crear directorio destino: {e}"
                )

        # 2. Instanciar Scanner
        # Pasamos config vacío ya que sync_path usa la sesión y source_id directo
        scanner = ScannerService("{}")

        for file in valid_files:
            try:
                # Sanitizar nombre de archivo si es necesario, por ahora confiamos en el filename original
                # pero aseguramos que sea solo nombre base
                safe_filename = os.path.basename(file.filename)
                file_path = os.path.join(target_dir, safe_filename)

                # Guardar archivo
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # Escanear inmediatamente en thread separado para no bloquear loop
                # sync_path(self, path: str, source_id: int = 1, force_scan: bool = True)
                await scanner.sync_path(file_path, source.id, True)

                saved_paths.append(safe_filename)
            except Exception as e:
                print(f"Error procesando {file.filename}: {e}")
                # Continuamos con los demás

    return {
        "success": True,
        "count": len(saved_paths),
        "files": saved_paths,
        "message": f"{len(saved_paths)} libros subidos y procesados correctamente",
    }


@router.get("/api/library/books/{book_id}")
async def get_book_detail(book_id: str, user_data: dict = Depends(require_mini_app_access)):
    """Retorna el detalle de un libro específico."""
    clean_id = int(book_id.replace("local_", ""))
    book = await LibraryService.get_book_by_id(clean_id)
    if not book:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    # Check if user has downloaded this book
    from repositories.download_repository import download_repo

    book["is_downloaded"] = await download_repo.has_user_downloaded(
        user_data["user_id"], book["title"], book.get("cleanTitle")
    )
    book["download_count"] = await download_repo.get_total_download_count(
        book["title"], book.get("cleanTitle")
    )
    return book


@router.patch("/api/library/books/{book_id}")
async def update_book(
    book_id: str, updates: dict[str, Any] = Body(...), user_data: dict = Depends(require_admin)
):
    """Actualiza metadatos de un libro (Admin only)."""
    try:
        clean_id = int(book_id.replace("local_", ""))
        success = await LibraryService.update_book_metadata(clean_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Libro no encontrado o error al actualizar")
        return {"success": True}
    except ValueError:
        raise HTTPException(status_code=400, detail="ID inválido")


@router.get("/api/library/regroup/suggestions")
async def get_regroup_suggestions(
    threshold: float = Query(0.8, ge=0.0, le=1.0), user_data: dict = Depends(require_admin)
):
    """
    Lista grupos de libros sugeridos para unificar en series.
    Busca similitudes en títulos y autor.
    """
    suggestions = await LibraryService.get_regroup_suggestions(threshold=threshold)
    return {"suggestions": suggestions}


@router.get("/api/library/orphans")
async def get_orphaned_books(
    limit: int = Query(100, ge=1, le=1000), user_data: dict = Depends(require_admin)
):
    """
    Lista libros que no tienen una serie asignada.
    Útil para detectar libros sueltos que deberían agruparse.
    """
    books = await LibraryService.get_books_without_series(limit=limit)
    return {"books": books}


@router.get("/api/library/catalog")
async def get_catalog(
    source_id: int | None = Query(None),
    folder: str | None = Query(None),
    series_hash: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    use_random_covers: bool = Query(True),
    sort_by: str = Query(
        "alpha",
        pattern="^(alpha|alpha_desc|date_added|date_added_desc|date_updated|date_updated_desc|downloads_desc|rating_desc)$",
    ),
    user_data: dict = Depends(require_mini_app_access),
):
    """Navega por la librería local simulando carpetas o agrupando por serie."""
    return await LibraryService.get_catalog(
        source_id=source_id,
        folder=folder,
        series_hash=series_hash,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        use_random_covers=use_random_covers,
    )


# ===== BACKUP ENDPOINTS =====
from services.backup_service import BackupService


@router.post("/api/library/backup")
async def create_backup(compress: bool = Query(True), user_data: dict = Depends(require_admin)):
    path = await BackupService.generate_backup_file(compress=compress)
    return {"success": True, "backup_path": path}


@router.get("/api/library/backups")
async def list_backups(user_data: dict = Depends(require_admin)):
    return {"backups": BackupService.list_backups(), "stats": BackupService.get_backup_stats()}


@router.post("/api/library/restore")
async def restore_backup(
    backup_filename: str = Query(...), user_data: dict = Depends(require_admin)
):
    # Restoration from PG SQL is complex via API, placeholder for now
    raise HTTPException(status_code=501, detail="Restauración SQL no disponible vía API todavía.")


@router.delete("/api/library/backups/{backup_filename}")
async def delete_backup(backup_filename: str, user_data: dict = Depends(require_admin)):
    return {"success": BackupService.delete_backup(backup_filename)}


# ===== EXPORT/IMPORT ENDPOINTS =====
from fastapi.responses import JSONResponse

from services.library_export_service import LibraryExportService


@router.get("/api/library/export")
async def export_library(
    source_id: int | None = Query(None),
    series: str | None = Query(None),
    user_data: dict = Depends(require_admin),
):
    return JSONResponse(
        content=LibraryExportService.export_library(source_id=source_id, series=series)
    )


@router.post("/api/library/import")
async def import_library(
    data: dict, merge: bool = Query(True), user_data: dict = Depends(require_admin)
):
    return {"success": True, "stats": LibraryExportService.import_from_json(data, merge=merge)}


# ===== MAINTENANCE ENDPOINTS =====
from services.library_maintenance_service import LibraryMaintenanceService


@router.post("/api/library/optimize")
async def optimize_database(user_data: dict = Depends(require_admin)):
    return LibraryMaintenanceService.optimize_database()


@router.post("/api/library/cleanup")
async def cleanup_orphaned_files(user_data: dict = Depends(require_admin)):
    return LibraryMaintenanceService.cleanup_orphaned_covers()


@router.get("/api/library/stats")
async def get_library_statistics(user_data: dict = Depends(require_mini_app_access)):
    return LibraryMaintenanceService.get_library_stats()


@router.get("/api/library/thumbnail/{filename}")
async def get_thumbnail(filename: str):
    original_path = os.path.join(COVERS_DIR, filename)
    thumb_path = os.path.join(THUMBNAILS_DIR, filename)
    if os.path.exists(thumb_path):
        return FileResponse(thumb_path)
    if not os.path.exists(original_path):
        raise HTTPException(status_code=404)
    try:
        with Image.open(original_path) as img:
            img.thumbnail((200, 300))
            img.save(thumb_path, optimize=True, quality=80)
        return FileResponse(thumb_path)
    except Exception:
        return FileResponse(original_path)
