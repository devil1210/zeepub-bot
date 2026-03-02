import asyncio
import logging
import os
import shutil
from typing import Any

from fastapi import HTTPException
from sqlalchemy import desc, func, select

from api.handlers.helpers import check_staff
from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.download_models import DownloadHistory
from models.library_models import (
    ArchivedBook,
    DuplicateBook,
    LocalBook,
    UploadHistory,
    UserDownload,
    UserRating,
)
from services.library_service import LibraryService
from services.scanner_service import ScannerService
from services.sync_service import SyncService
from utils.library_db import COVERS_DIR, engine, get_session, init_library_db

logger = logging.getLogger(__name__)


async def handle_admin_backup_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Syncs everything (Users, Levels, and Library) to Supabase - Full Backup."""
    check_staff(user_data)
    if not config.ENABLE_SUPABASE:
        return {"success": False, "message": "Supabase no está habilitado."}

    client = supabase_manager.get_client()
    if not client:
        return {"success": False, "message": "Supabase no está configurado"}

    logger.info("ADMIN: Starting FULL BACKUP to Supabase...")
    from api.handlers.admin.user_handlers import handle_admin_sync_users_cloud

    res_users = await handle_admin_sync_users_cloud({}, user_data)
    res_library = await handle_admin_sync_library_cloud({}, user_data)

    if res_users.get("success") and res_library.get("success"):
        return {
            "success": True,
            "message": "Respaldo completo realizado con éxito en Supabase.",
            "details": {"users": res_users.get("stats"), "library": res_library.get("stats")},
        }
    return {"success": False, "message": "El respaldo se realizó parcialmente con errores."}


async def handle_admin_sync_library_cloud(data: dict[str, Any], user_data: dict[str, Any]):
    """Sincroniza metadatos de series, propuestas IA, feedback, fuentes y libros locales con Supabase."""
    check_staff(user_data)
    return await SyncService.sync_library_to_cloud()


async def handle_admin_scan_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced library scan."""
    check_staff(user_data)
    force = data.get("force", False)
    soft = data.get("soft", False)

    if ScannerService._is_scanning:
        return {"success": False, "message": "⚠️ Ya hay un escaneo de librería en progreso."}

    libs_json = os.getenv("LOCAL_LIBRARIES")
    if not libs_json:
        return {"success": False, "message": "LOCAL_LIBRARIES no configurada."}

    scanner = ScannerService(libs_json)
    # 🛠️ CORRECCIÓN: Usar asyncio.create_task en el loop principal en lugar de nuevo thread+loop
    asyncio.create_task(scanner.sync_all(force_scan=force, soft_scan=soft))
    return {"success": True, "message": "Escaneo iniciado en segundo plano."}


async def handle_admin_cleanup_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Checks for physical existence of all books and cleans up the database."""
    check_staff(user_data)
    try:
        async with pg_manager.get_session() as session:
            stats = await ScannerService.cleanup_library_orphans(session, user_id=user_data.get("user_id"))
            return {
                "success": True,
                "message": f"Limpieza completada: Se eliminaron {stats['deleted_books']} libros.",
                "stats": stats,
            }
    except Exception as e:
        logger.error(f"Error during library cleanup: {e}")
        return {"success": False, "message": f"Error during cleanup: {str(e)}"}


async def handle_admin_scan_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced scan for a specific series."""
    check_staff(user_data)
    series_hash = data.get("series_hash")
    force = data.get("force", True)
    if not series_hash:
        return {"success": False, "message": "series_hash es requerido."}

    if ScannerService._is_scanning:
        return {"success": False, "message": "⚠️ Ya hay un escaneo de librería en progreso."}

    libs_json = os.getenv("LOCAL_LIBRARIES")
    scanner = ScannerService(libs_json or "{}")
    # 🛠️ CORRECCIÓN: Usar asyncio.create_task
    asyncio.create_task(scanner.sync_series(series_hash, force_scan=force))
    return {"success": True, "message": "Sincronización de serie iniciada en segundo plano."}


async def handle_admin_scan_status(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    return {"success": True, "is_scanning": ScannerService._is_scanning, "progress": ScannerService._current_progress}


async def handle_admin_stop_scan(data: dict[str, Any], user_data: dict[str, Any]):
    """Stops the current scan."""
    check_staff(user_data)
    success = ScannerService.stop_scan()
    return {"success": success, "message": "Escaneo detenido." if success else "No hay escaneo en curso."}


async def handle_admin_reset_library(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    if not data.get("confirmed", False):
        return {"success": False, "message": "Confirmación requerida.", "requireConfirmation": True}

    try:
        import sqlalchemy as sa

        items_deleted = []
        with engine.begin() as conn:
            for table in [
                "user_ratings",
                "user_downloads",
                "metadata_proposals",
                "ai_learning_feedback",
                "local_books",
                "series_metadata",
                "library_sources",
                "duplicate_books",
                "upload_books",
            ]:
                conn.execute(sa.text(f"DELETE FROM {table}"))
            items_deleted.append("Tablas de PostgreSQL limpiadas")

        if os.path.exists(COVERS_DIR):
            shutil.rmtree(COVERS_DIR)
            os.makedirs(COVERS_DIR, exist_ok=True)
            items_deleted.append("Directorio de portadas reseteado")

        init_library_db()
        items_deleted.append("Esquema de base de datos recreado")
        return {"success": True, "message": "Base de datos local reseteada exitosamente.", "details": items_deleted}
    except Exception as e:
        logger.error(f"Error reset library: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_find_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    session = get_session()
    try:
        duplicate_hashes = (
            session.query(LocalBook.book_hash, func.count().label("count"))
            .filter(LocalBook.book_hash.isnot(None))
            .group_by(LocalBook.book_hash)
            .having(func.count() > 1)
            .all()
        )
        duplicate_groups = []
        total_wasted_space = 0
        for hash_row in duplicate_hashes:
            content_hash = hash_row[0]
            books = (
                session.query(LocalBook)
                .filter(LocalBook.book_hash == content_hash)
                .order_by(LocalBook.indexed_at.asc())
                .all()
            )
            if len(books) <= 1:
                continue
            file_sizes = [b.file_size or 0 for b in books]
            wasted = sum(file_sizes) - min(file_sizes)
            total_wasted_space += wasted
            duplicate_groups.append(
                {
                    "book_hash": content_hash,
                    "title": books[0].title,
                    "count": len(books),
                    "total_size": sum(file_sizes),
                    "wasted_space": wasted,
                    "books": [
                        {
                            "id": b.id,
                            "filepath": b.filepath,
                            "filename": b.filename,
                            "file_size": b.file_size or 0,
                            "indexed_at": b.indexed_at.isoformat() if b.indexed_at else None,
                        }
                        for b in books
                    ],
                }
            )
        duplicate_groups.sort(key=lambda x: x["wasted_space"], reverse=True)
        return {
            "success": True,
            "duplicate_groups": duplicate_groups,
            "summary": {
                "total_duplicates": len(duplicate_hashes),
                "wasted_space_mb": round(total_wasted_space / (1024 * 1024), 2),
            },
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        session.close()


async def handle_admin_delete_duplicate(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    book_ids = data.get("book_ids", [])
    if not book_ids:
        return {"success": False, "message": "No se especificaron libros"}
    session = get_session()
    try:
        books = session.query(LocalBook).filter(LocalBook.id.in_(book_ids)).all()
        count = 0
        for book in books:
            if book.filepath and os.path.exists(book.filepath):
                os.remove(book.filepath)
            session.query(DownloadHistory).filter_by(book_id=book.id).update({DownloadHistory.book_id: None})
            session.query(UserDownload).filter_by(book_id=book.id).update({UserDownload.book_id: None})
            session.query(UserRating).filter_by(book_id=book.id).update({UserRating.book_id: None})
            session.delete(book)
            count += 1
        session.commit()
        return {"success": True, "deleted_count": count}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        session.close()


async def handle_admin_delete_duplicate_item(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    dup_id, target = data.get("id"), data.get("target")
    session = get_session()
    try:
        dup = session.query(DuplicateBook).filter_by(id=dup_id).first()
        if not dup:
            return {"success": False, "message": "No encontrado"}
        path = dup.original_filepath if target == "original" else dup.duplicate_filepath
        if path and os.path.exists(path):
            os.remove(path)
        if target == "original":
            book = session.query(LocalBook).filter_by(filepath=path).first()
            if book:
                session.add(
                    ArchivedBook(
                        series_hash=book.series_hash,
                        book_hash=book.book_hash,
                        title=book.title,
                        filename=book.filename,
                        last_filepath=book.filepath,
                        original_book_id=book.id,
                        reason="manual_duplicate_resolution",
                    )
                )
                session.delete(book)
        session.delete(dup)
        session.commit()
        return {"success": True, "message": "Eliminado correctamente"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        session.close()


async def handle_admin_get_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    session = get_session()
    try:
        dups = session.query(DuplicateBook).order_by(desc(DuplicateBook.detected_at)).all()
        return {
            "success": True,
            "duplicates": [
                {
                    "id": d.id,
                    "title": d.title,
                    "author": d.author,
                    "hash": d.book_hash,
                    "original": d.original_filepath,
                    "duplicate": d.duplicate_filepath,
                    "detectedAt": d.detected_at.isoformat() if d.detected_at else None,
                }
                for d in dups
            ],
        }
    finally:
        session.close()


async def handle_admin_recheck_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    session = get_session()
    try:
        dups, removed = session.query(DuplicateBook).all(), 0
        for d in dups:
            if not os.path.exists(d.duplicate_filepath) or not os.path.exists(d.original_filepath):
                session.delete(d)
                removed += 1
        session.commit()
        return {"success": True, "removed_count": removed}
    finally:
        session.close()


async def handle_admin_clear_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    session = get_session()
    session.query(DuplicateBook).delete()
    session.commit()
    session.close()
    return {"success": True}


async def handle_admin_ai_series_duplicate_scan(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    if LibraryService._is_ai_scanning:
        return {"success": False, "message": "Ya en curso."}

    async def run_ai_scan():
        try:
            LibraryService._is_ai_scanning = True
            await LibraryService.find_ai_series_duplicates()
        except Exception as e:
            logger.error(f"AI scan task error: {e}")
        finally:
            LibraryService._is_ai_scanning = False

    asyncio.create_task(run_ai_scan())
    return {"success": True, "message": "Iniciado en segundo plano."}


async def handle_admin_get_ai_scan_status(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    return {"success": True, "is_scanning": LibraryService._is_ai_scanning}


async def handle_admin_merge_series(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    try:
        success = await LibraryService.merge_series(
            data.get("target_hash"), data.get("source_hash"), data.get("new_name")
        )
        return {"success": success}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_bulk_upload_confirm(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    selected_ids = data.get("selected_ids", []) or data.get("upload_ids", [])
    discarded_ids = data.get("discarded_ids", [])
    if not selected_ids and not discarded_ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    from pathlib import Path

    from handlers.epub_upload_handler import epub_uploader, pending_uploads

    for disc_id in discarded_ids:
        if disc_id in pending_uploads:
            epub_uploader.cleanup_upload(disc_id, Path(pending_uploads[disc_id]["file_path"]))

    results = []
    for upload_id in selected_ids:
        if upload_id not in pending_uploads:
            continue
        info = pending_uploads[upload_id]
        f_path, meta = Path(info["file_path"]), info["metadata"]
        try:
            success = await epub_uploader.add_to_library(f_path, meta.get("suggested_path"), meta)
            status = "success" if success else "error"
            epub_uploader._log_history(
                user_id=info["user_id"],
                filename=info["original_filename"],
                book_hash=meta.get("book_hash"),
                status=status,
                final_path=meta.get("suggested_path") if success else None,
            )
            if success:
                epub_uploader.cleanup_upload(upload_id, f_path)
            results.append({"upload_id": upload_id, "success": success})
        except Exception as e:
            results.append({"upload_id": upload_id, "success": False, "error": str(e)})
    return {"success": True, "results": results}


async def handle_get_upload_history(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    async with pg_manager.get_session() as session:
        stmt = (
            select(UploadHistory)
            .order_by(desc(UploadHistory.created_at))
            .limit(data.get("limit", 100))
            .offset(data.get("offset", 0))
        )
        res = (await session.execute(stmt)).scalars().all()
        return {
            "history": [
                {
                    "id": i.id,
                    "user_id": i.user_id,
                    "filename": i.filename,
                    "status": i.status,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in res
            ]
        }


async def handle_admin_enrich_metadata(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    from services.maintenance.orchestrator import MaintenanceOrchestrator

    # Iniciar en segundo plano
    asyncio.create_task(MaintenanceOrchestrator.run_tool("metadata_enrich"))

    return {"success": True, "message": "Enriquecimiento en segundo plano iniciado."}


async def handle_admin_update_covers(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates background book cover update for all books."""
    check_staff(user_data)

    from services.maintenance.orchestrator import MaintenanceOrchestrator

    # Iniciar en segundo plano sin esperar
    asyncio.create_task(MaintenanceOrchestrator.run_tool("cover_refresh"))

    return {"success": True, "message": "Actualización de portadas iniciada en segundo plano."}


async def handle_admin_fix_integrity(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates background database integrity check for series linkage."""
    check_staff(user_data)

    from services.maintenance.orchestrator import MaintenanceOrchestrator

    # Iniciar en segundo plano
    asyncio.create_task(MaintenanceOrchestrator.run_tool("db_integrity"))

    return {"success": True, "message": "Corrección de integridad iniciada en segundo plano."}
