import asyncio
import json
import logging
import os
import shutil
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, text

from api.handlers.helpers import check_staff
from config.config_settings import config
from core.db_manager_pg import pg_manager
from core.supabase_manager import supabase_manager
from models.library import (
    ArchivedBook,
    DuplicateBook,
)
from repositories.book_repository import book_repo
from repositories.duplicate_repository import duplicate_repo
from repositories.upload_repository import upload_repo
from services.library_service import LibraryService
from services.scanner_service import ScannerService
from services.sync_service import SyncService
from services.upload_service import upload_service
from utils.library_db import COVERS_DIR

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
            "details": {
                "users": res_users.get("stats"),
                "library": res_library.get("stats"),
            },
        }
    return {
        "success": False,
        "message": "El respaldo se realizó parcialmente con errores.",
    }


async def handle_admin_sync_library_cloud(
    data: dict[str, Any], user_data: dict[str, Any]
):
    """Sincroniza metadatos de series, propuestas IA, feedback, fuentes y libros locales con Supabase."""
    check_staff(user_data)
    return await SyncService.sync_library_to_cloud()


async def handle_admin_scan_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced library scan.

    Params:
      force (bool): Re-procesa todos los EPUBs aunque ya esten en DB.
      soft (bool): Solo procesa archivos modificados en 24h.
      max_files (int): Limite de EPUBs a procesar. 0 = sin limite (diagnostico rapido).
    """
    check_staff(user_data)
    force = data.get("force", False)
    soft = data.get("soft", False)
    max_files = int(data.get("max_files", 0))

    if ScannerService._is_scanning:
        return {
            "success": False,
            "message": "Ya hay un escaneo de libreria en progreso.",
        }

    libs_json = os.getenv("LOCAL_LIBRARIES")
    if not libs_json:
        return {"success": False, "message": "LOCAL_LIBRARIES no configurada."}

    scanner = ScannerService(libs_json)
    if max_files > 0:
        logger.info(f"[quick-scan] Modo diagnostico: maximo {max_files} EPUBs.")
    asyncio.create_task(
        scanner.sync_all(force_scan=force, soft_scan=soft, max_files=max_files)
    )
    mode = f"diagnostico ({max_files} EPUBs)" if max_files > 0 else "completo"
    return {"success": True, "message": f"Escaneo {mode} iniciado en segundo plano."}


async def handle_admin_cleanup_library(data: dict[str, Any], user_data: dict[str, Any]):
    """Checks for physical existence of all books and cleans up the database."""
    check_staff(user_data)
    try:
        async with pg_manager.get_session() as session:
            stats = await ScannerService.cleanup_library_orphans(
                session, user_id=user_data.get("user_id")
            )
            return {
                "success": True,
                "message": f"Limpieza completada: Se eliminaron {stats['deleted_books']} libros.",
                "stats": stats,
            }
    except Exception as e:
        logger.error(f"Error during library cleanup: {e}", exc_info=True)
        return {"success": False, "message": f"Error during cleanup: {str(e)}"}


async def handle_admin_scan_series(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates forced scan for a specific series."""
    check_staff(user_data)
    series_hash = data.get("series_hash")
    force = data.get("force", True)
    if not series_hash:
        return {"success": False, "message": "series_hash es requerido."}

    if ScannerService._is_scanning:
        return {
            "success": False,
            "message": "⚠️ Ya hay un escaneo de librería en progreso.",
        }

    libs_json = os.getenv("LOCAL_LIBRARIES")
    scanner = ScannerService(libs_json or "{}")
    # 🛠️ CORRECCIÓN: Usar asyncio.create_task
    asyncio.create_task(scanner.sync_series(series_hash, force_scan=force))
    return {
        "success": True,
        "message": "Sincronización de serie iniciada en segundo plano.",
    }


async def handle_admin_scan_status(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    return {
        "success": True,
        "is_scanning": ScannerService._is_scanning,
        "progress": ScannerService._current_progress,
    }


async def handle_admin_stop_scan(data: dict[str, Any], user_data: dict[str, Any]):
    """Stops the current scan."""
    check_staff(user_data)
    success = ScannerService.stop_scan()
    return {
        "success": success,
        "message": "Escaneo detenido." if success else "No hay escaneo en curso.",
    }


async def handle_admin_reset_library(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    if not data.get("confirmed", False):
        return {
            "success": False,
            "message": "Confirmación requerida.",
            "requireConfirmation": True,
        }

    try:
        items_deleted = []
        async with pg_manager.get_session() as session:
            for table in [
                "user_ratings",
                "user_downloads",
                "metadata_proposals",
                "ai_learning_feedback",
                "books",
                "series",
                "library_sources",
                "duplicate_books",
                "upload_books",
            ]:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            await session.commit()
            items_deleted.append("Tablas de PostgreSQL truncadas (CASCADE)")

        if os.path.exists(COVERS_DIR):
            shutil.rmtree(COVERS_DIR)
            os.makedirs(COVERS_DIR, exist_ok=True)
            items_deleted.append("Directorio de portadas reseteado")

        from utils.library_db import init_library_db

        init_library_db()
        items_deleted.append("Esquema de base de datos verificado")

        return {
            "success": True,
            "message": "Base de datos local reseteada exitosamente.",
            "details": items_deleted,
        }
    except Exception as e:
        logger.error(f"Error reset library: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_find_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    try:
        async with pg_manager.get_session() as _:
            duplicate_hashes = await book_repo.get_duplicate_hashes()
            duplicate_groups = []
            total_wasted_space = 0

            for content_hash, _ in duplicate_hashes:
                books = await book_repo.get_books_by_hash(content_hash)

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
                                "indexed_at": b.indexed_at.isoformat()
                                if b.indexed_at
                                else None,
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
        logger.error(f"Error finding duplicates: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_delete_duplicate(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    book_ids = data.get("book_ids", [])
    if not book_ids:
        return {"success": False, "message": "No se especificaron libros"}

    try:
        count = 0
        for book_id in book_ids:
            book = await book_repo.get_by_id(book_id)
            if not book:
                continue

            if book.filepath and os.path.exists(book.filepath):
                try:
                    os.remove(book.filepath)
                except Exception as fe:
                    logger.warning(
                        f"Could not delete physical file {book.filepath}: {fe}"
                    )

            success = await book_repo.delete(book_id)
            if success:
                count += 1
        return {"success": True, "deleted_count": count}
    except Exception as e:
        logger.error(f"Error deleting duplicate: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_delete_duplicate_item(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    dup_id, target = data.get("id"), data.get("target")
    try:
        async with pg_manager.get_session() as session:
            stmt = select(DuplicateBook).where(DuplicateBook.id == dup_id)
            dup = (await session.execute(stmt)).scalar_one_or_none()
            if not dup:
                return {"success": False, "message": "No encontrado"}

            path = (
                dup.original_filepath
                if target == "original"
                else dup.duplicate_filepath
            )
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Could not remove file at {path}: {e}")

            if target == "original":
                book = await book_repo.get_by_filepath(path)
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
                    await book_repo.delete(book.id)

            await session.delete(dup)
            await session.commit()
            return {"success": True, "message": "Eliminado correctamente"}
    except Exception as e:
        logger.error(f"Error deleting duplicate item: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_get_duplicates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    try:
        dups = await duplicate_repo.get_all_duplicates()
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
    except Exception as e:
        logger.error(f"Error getting duplicates: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_recheck_duplicates(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    try:
        async with pg_manager.get_session() as session:
            stmt = select(DuplicateBook)
            dups = (await session.execute(stmt)).scalars().all()
            removed = 0
            for d in dups:
                if not os.path.exists(d.duplicate_filepath or "") or not os.path.exists(
                    d.original_filepath or ""
                ):
                    await session.delete(d)
                    removed += 1
            await session.commit()
            return {"success": True, "removed_count": removed}
    except Exception as e:
        logger.error(f"Error rechecking duplicates: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_clear_duplicates(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    try:
        success = await duplicate_repo.clear_all()
        return {"success": success}
    except Exception as e:
        logger.error(f"Error clearing duplicates: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_ai_series_duplicate_scan(
    data: dict[str, Any], user_data: dict[str, Any]
):
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


async def handle_admin_get_ai_scan_status(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    return {"success": True, "is_scanning": LibraryService._is_ai_scanning}


async def handle_admin_merge_series(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    try:
        success = await LibraryService.merge_series(
            data.get("target_hash"), data.get("source_hash"), data.get("new_name")
        )
        if success:
            SyncService.trigger_auto_sync()
        return {"success": success}
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_add_series_alias(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    series_id = data.get("series_id") or data.get("target_hash")
    alias = data.get("alias")
    res = await LibraryService.add_series_alias(series_id, alias)
    if res.get("success"):
        SyncService.trigger_auto_sync()
    return res


async def handle_admin_delete_series_alias(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    alias_id = data.get("alias_id")
    if not alias_id:
        return {"success": False, "message": "Falta alias_id"}
    res = await LibraryService.delete_series_alias(int(alias_id))
    if res.get("success"):
        SyncService.trigger_auto_sync()
    return res


async def handle_admin_bulk_upload_confirm(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    selected_ids = data.get("selected_ids", []) or data.get("upload_ids", [])
    discarded_ids = data.get("discarded_ids", [])
    if not selected_ids and not discarded_ids:
        raise HTTPException(status_code=400, detail="No IDs provided")

    from pathlib import Path

    from handlers.epub_upload_handler import pending_uploads

    # Clean up discarded
    for disc_id in discarded_ids:
        if disc_id in pending_uploads:
            info = pending_uploads[disc_id]
            f_p = Path(info["file_path"])
            if f_p.exists():
                try:
                    f_p.unlink()
                except Exception:
                    pass
            del pending_uploads[disc_id]
        else:
            # Limpiar desde la DB si no está en memoria
            try:
                db_id = int(str(disc_id)) if str(disc_id).isdigit() else None
                if db_id:
                    record = await upload_repo.get_upload_by_id(db_id)
                    if record:
                        temp_path = Path(record.temp_filepath)
                        if temp_path.exists():
                            try:
                                temp_path.unlink()
                            except Exception:
                                pass
                        await upload_repo.delete_upload_record(db_id)
            except Exception as e:
                logger.error(f"Error descartando bulk upload {disc_id} de DB: {e}")

    results = []
    for upload_id in selected_ids:
        info = None
        if upload_id in pending_uploads:
            info = pending_uploads[upload_id]
        else:
            # Fallback a DB
            try:
                db_id = int(str(upload_id)) if str(upload_id).isdigit() else None
                if db_id:
                    record = await upload_repo.get_upload_by_id(db_id)
                    if record:
                        info = {
                            "file_path": record.temp_filepath,
                            "metadata": record.upload_metadata,
                            "user_id": record.telegram_id,
                            "original_filename": record.original_filename,
                        }
            except Exception as e:
                logger.error(f"Error recuperando bulk upload {upload_id} de DB: {e}")

        if not info:
            logger.warning(f"Upload ID {upload_id} no encontrado en memoria ni DB.")
            results.append(
                {"upload_id": upload_id, "success": False, "error": "No encontrado"}
            )
            continue

        f_path = Path(info["file_path"])
        meta = info["metadata"]

        try:
            # Use UploadService for robustness
            success = await upload_service.finalize_upload(
                f_path, meta.get("suggested_path"), meta
            )

            status = "success" if success else "error"

            # Log history via repository
            await upload_repo.log_history(
                {
                    "user_id": info["user_id"],
                    "filename": info["original_filename"],
                    "book_hash": meta.get("book_hash"),
                    "status": status,
                    "final_path": meta.get("suggested_path") if success else None,
                }
            )

            if success:
                # El archivo ya es borrado por finalize_upload, pero por si acaso
                if f_path.exists():
                    try:
                        f_path.unlink()
                    except Exception:
                        pass

                if upload_id in pending_uploads:
                    del pending_uploads[upload_id]

            results.append({"upload_id": upload_id, "success": success})

        except Exception as e:
            logger.error(
                f"Error finalizing bulk upload {upload_id}: {e}", exc_info=True
            )
            results.append({"upload_id": upload_id, "success": False, "error": str(e)})

    return {"success": True, "results": results}


async def handle_get_upload_history(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    limit = data.get("limit", 100)
    offset = data.get("offset", 0)
    history_entries = await upload_repo.get_history(limit=limit, offset=offset)

    return {
        "history": [
            {
                "id": i.id,
                "user_id": i.user_id,
                "filename": i.filename,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in history_entries
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

    return {
        "success": True,
        "message": "Actualización de portadas iniciada en segundo plano.",
    }


async def handle_admin_fix_integrity(data: dict[str, Any], user_data: dict[str, Any]):
    """Activates background database integrity check for series linkage."""
    check_staff(user_data)

    from services.maintenance.orchestrator import MaintenanceOrchestrator

    # Iniciar en segundo plano
    asyncio.create_task(MaintenanceOrchestrator.run_tool("db_integrity"))

    return {
        "success": True,
        "message": "Corrección de integridad iniciada en segundo plano.",
    }


async def handle_admin_get_genre_audits(
    data: dict[str, Any], user_data: dict[str, Any]
):
    """Returns all pending metadata audits (unresolved)."""
    check_staff(user_data)
    try:
        async with pg_manager.get_session() as session:
            stmt = text("""
                SELECT id, series_hash, series_name, change_type, old_value, new_value, created_at, status
                FROM metadata_audits
                WHERE status = 'pending' OR status IS NULL
                ORDER BY created_at DESC
            """)
            result = await session.execute(stmt)
            audits = []
            for row in result:
                audits.append(
                    {
                        "id": row.id,
                        "series_hash": row.series_hash,
                        "series_name": row.series_name,
                        "change_type": row.change_type,
                        "old_value": row.old_value
                        if isinstance(row.old_value, dict)
                        else json.loads(row.old_value or "{}"),
                        "new_value": row.new_value
                        if isinstance(row.new_value, dict)
                        else json.loads(row.new_value or "{}"),
                        "created_at": row.created_at.isoformat()
                        if row.created_at
                        else None,
                    }
                )
            return {"success": True, "audits": audits}
    except Exception as e:
        logger.error(f"Error fetching genre audits: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_admin_resolve_genre_audit(
    data: dict[str, Any], user_data: dict[str, Any]
):
    """Marks an audit as resolved."""
    check_staff(user_data)
    audit_id = data.get("audit_id")
    if not audit_id:
        return {"success": False, "message": "audit_id es requerido."}

    try:
        async with pg_manager.get_session() as session:
            stmt = text(
                "UPDATE metadata_audits SET status = 'reviewed', reviewed_at = NOW() WHERE id = :id"
            )
            await session.execute(stmt, {"id": audit_id})
            await session.commit()
            return {"success": True, "message": "Auditoría marcada como revisada."}
    except Exception as e:
        logger.error(f"Error resolving genre audit {audit_id}: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


async def handle_upload_confirm_internal(
    data: dict[str, Any], user_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Confirma un upload individual desde la Web App REST.
    Mueve el archivo a su destino final (Nextcloud o disco local) y lo indexa.
    Reutiliza la lógica de finalize_upload de UploadService.
    """
    from pathlib import Path

    from handlers.epub_upload_handler import pending_uploads

    upload_id = data.get("upload_id")
    if not upload_id:
        raise HTTPException(status_code=400, detail="upload_id es requerido")

    # Buscar en memoria primero, luego en la DB
    info = pending_uploads.get(str(upload_id))
    if not info:
        try:
            db_id = int(str(upload_id)) if str(upload_id).isdigit() else None
            if db_id:
                record = await upload_repo.get_upload_by_id(db_id)
                if record:
                    info = {
                        "file_path": record.temp_filepath,
                        "metadata": record.upload_metadata or {},
                        "user_id": record.telegram_id,
                        "original_filename": record.original_filename,
                    }
        except Exception as e:
            logger.error(f"Error recuperando upload {upload_id} de DB: {e}")

    if not info:
        raise HTTPException(
            status_code=404, detail=f"Upload ID {upload_id} no encontrado"
        )

    f_path = Path(info["file_path"])
    meta = info.get("metadata") or {}

    # Si el frontend mandó un path personalizado, usarlo
    if data.get("path"):
        meta["suggested_path"] = data["path"]

    try:
        success = await upload_service.finalize_upload(
            f_path, meta.get("suggested_path"), meta
        )

        status = "success" if success else "error"
        await upload_repo.log_history(
            {
                "user_id": info.get("user_id", 0),
                "filename": info.get("original_filename", "unknown"),
                "book_hash": meta.get("book_hash"),
                "status": status,
                "final_path": meta.get("suggested_path") if success else None,
            }
        )

        if success and f_path.exists():
            f_path.unlink(missing_ok=True)

        if str(upload_id) in pending_uploads:
            del pending_uploads[str(upload_id)]

        return {"success": success, "upload_id": upload_id}

    except Exception as e:
        logger.error(f"Error finalizando upload {upload_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error al finalizar el upload: {str(e)}"
        )


async def handle_admin_get_series_detail(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """Retorna los datos completos de una serie (metadatos, alias y volúmenes) para edición."""
    check_staff(user_data)
    series_id = (data.get("series_id") or data.get("id") or data.get("series_hash") or "").strip()
    if not series_id:
        return {"success": False, "message": "ID de serie requerido"}

    from sqlalchemy import or_
    from sqlalchemy.orm import selectinload
    from models.library import Series, Book

    async with pg_manager.get_session() as session:
        stmt = (
            select(Series)
            .options(
                selectinload(Series.aliases),
                selectinload(Series.books)
            )
            .where(
                or_(
                    Series.id == series_id,
                    Series.series_hash == series_id,
                    Series.slug == series_id
                )
            )
        )
        result = await session.execute(stmt)
        series = result.scalar_one_or_none()
        if not series:
            return {"success": False, "message": "Serie no encontrada"}

        return {
            "success": True,
            "series": {
                "id": series.id,
                "series_hash": series.series_hash or series.id,
                "name": series.name or series.series_name or "Sin Título",
                "series_spanish": series.series_spanish or series.name_spanish or "",
                "series_english": series.series_english or series.name_english or "",
                "slug": series.slug or "",
                "author": series.author or "",
                "illustrator": series.illustrator or "",
                "description": series.description or "",
                "publisher": series.publisher or "",
                "book_type": series.book_type or "Novela Ligera",
                "cover_url": series.cover_url or "",
                "book_count": series.book_count or len(series.books or []),
                "aliases": [{"id": a.id, "alias": a.alias} for a in (series.aliases or [])],
                "books": [
                    {
                        "id": b.id,
                        "title": b.title,
                        "volume": b.volume,
                        "translator": b.translator or "",
                        "layout_by": b.layout_by or "",
                        "cover_url": b.cover_low or b.cover_medium
                    }
                    for b in (series.books or [])
                ]
            }
        }

