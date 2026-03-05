import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from sqlalchemy import select, text

from config.config_settings import config
from core.db_manager_pg import pg_manager
from models.library_models import LibrarySource, LocalBook
from services.maintenance.orchestrator import MaintenanceOrchestrator
from services.notification_service import notification_service
from services.scanner.epub_scanner import EpubScanner
from services.scanner.library_scanner import LibraryScanner
from services.scanner.series_scanner import SeriesScanner

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Servicio de orquestación para el escaneo de la librería.
    Mantiene el estado global del progreso y coordina los sub-escáneres.
    """

    def __init__(self, libraries: str | dict | None = None, *args, **kwargs):
        """
        Inicializa el servicio.
        """
        if isinstance(libraries, str):
            try:
                import json

                self.libraries = json.loads(libraries)
            except Exception:
                self.libraries = None
        else:
            self.libraries = libraries

    _is_scanning = False
    _stop_requested = False
    _current_progress = {
        "status": "idle",
        "scanned": 0,
        "added": 0,
        "updated": 0,
        "removed": 0,
        "total": 0,
    }

    @classmethod
    def get_status(cls):
        return cls._current_progress

    async def sync_all(self, force_scan: bool = False, soft_scan: bool = False, max_files: int = 0) -> dict[str, Any] | None:
        """
        Escanea todas las rutas locales configuradas en busca de nuevos libros.
        max_files: si > 0, procesa solo ese número de EPUBs (modo diagnóstico rápido).
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso.")
            return None

        ScannerService._is_scanning = True
        ScannerService._stop_requested = False
        ScannerService._current_progress.update(
            {
                "status": "scanning",
                "scanned": 0,
                "added": 0,
                "updated": 0,
                "removed": 0,
                "archived": 0,
                "total": 0,
            }
        )

        results = {
            "sources_scanned": 0,
            "total_scanned": 0,
            "added": 0,
            "updated": 0,
            "removed": 0,
            "archived": 0,
            "touched_series_hashes": set(),
        }

        all_new_books = []

        try:
            async with pg_manager.get_session() as session:
                local_libs_map = getattr(self, "libraries", None)

                # Si no se pasó mapa, intentar obtener de config (compatibilidad) o DB
                if not local_libs_map:
                    if hasattr(config, "LOCAL_LIBRARIES"):
                        local_libs_map = config.LOCAL_LIBRARIES
                    else:
                        # Obtener de tabla LibrarySource (la fuente de verdad ahora)
                        stmt_sources = select(LibrarySource)
                        res_sources = await session.execute(stmt_sources)
                        db_sources = res_sources.scalars().all()
                        if db_sources:
                            local_libs_map = {s.name: s.path for s in db_sources}
                        else:
                            # Fallback extremo
                            local_libs_map = {"Main": "data/library/downloads"}

                for name, path in local_libs_map.items():
                    if ScannerService._stop_requested:
                        break

                    path = os.path.abspath(path)
                    os.makedirs(path, exist_ok=True)

                    # Obtener fuente
                    stmt_source = select(LibrarySource).where(LibrarySource.path == path)
                    res_source = await session.execute(stmt_source)
                    source = res_source.scalar_one_or_none()

                    if not source:
                        source = LibrarySource(name=name, path=path)
                        session.add(source)
                        await session.flush()

                    source_results, found_files = await self._scan_directory(source, session, force_scan, soft_scan, max_files=max_files)
                    results["sources_scanned"] += 1

                    if "added_books_details" in source_results:
                        all_new_books.extend(source_results["added_books_details"])

                    # Acumular resultados
                    for k, v in source_results.items():
                        if k == "touched_series_hashes":
                            results[k].update(v)
                        elif isinstance(v, (int, float)):
                            results[k] = results.get(k, 0) + v

                    # Pruning
                    if not soft_scan:
                        archived, removed = await LibraryScanner.prune_source(session, source, found_files)
                        results["archived"] += archived
                        results["removed"] += removed
                        source.last_scanned = datetime.utcnow()
                        await session.commit()

                # Orphan Check
                if results["sources_scanned"] > 0:
                    stmt_scanned = select(LibrarySource.id).where(LibrarySource.path.in_(local_libs_map.values()))
                    res_scanned = await session.execute(stmt_scanned)
                    scanned_ids = [row[0] for row in res_scanned]

                    detected, moved = await LibraryScanner.resolve_orphans(session, scanned_ids)
                    results["removed"] += detected

                # AI Gardener
                if results["touched_series_hashes"]:
                    await SeriesScanner.run_ai_gardener(session, results["touched_series_hashes"])

                # Sync Book Counts
                await session.execute(
                    text("""
                        UPDATE series_metadata sm
                        SET book_count = (SELECT COUNT(*) FROM local_books lb WHERE lb.series_hash = sm.series_hash)
                    """)
                )
                await session.commit()

            # Notificar
            if all_new_books:
                asyncio.create_task(notification_service.notify_new_books(all_new_books))

            # Auto-heal
            logger.info("🛠️ Ejecutando auto-correcciones de integridad y slugs...")
            await MaintenanceOrchestrator.run_tool("db_integrity")
            await MaintenanceOrchestrator.run_tool("slug_recalculate")

            final_status = "cancelled" if ScannerService._stop_requested else "completed"
            ScannerService._current_progress.update(
                {
                    "status": final_status,
                    "results": results,
                    "last_run": datetime.utcnow().isoformat(),
                }
            )
            return results

        except Exception as e:
            logger.error(f"Error en sync_all: {e}")
            ScannerService._current_progress.update(
                {
                    "status": "error",
                    "error_message": str(e),
                    "last_run": datetime.utcnow().isoformat(),
                }
            )
            return None
        finally:
            ScannerService._is_scanning = False

    async def _scan_directory(self, source, session, force_scan=False, soft_scan=False, max_files: int = 0) -> tuple:
        results = {
            "total_scanned": 0,
            "added": 0,
            "updated": 0,
            "duplicates": 0,
            "failed": 0,
            "touched_series_hashes": set(),
            "added_books_details": [],
        }
        found_files = set()

        for root, _, files in os.walk(source.path):
            if ScannerService._stop_requested:
                break

            for file in files:
                if ScannerService._stop_requested:
                    break

                if not file.lower().endswith(".epub"):
                    continue

                full_path = os.path.abspath(os.path.join(root, file))
                found_files.add(full_path)
                results["total_scanned"] += 1

                # Modo diagnóstico: cortar tras N archivos
                if max_files > 0 and results["total_scanned"] > max_files:
                    logger.info(f"[quick-scan] Límite de {max_files} archivos alcanzado.")
                    break

                if soft_scan:
                    mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
                    # Skip if older than 24h and already in DB
                    if (datetime.now() - mtime).total_seconds() > 86400:
                        stmt_exists = select(LocalBook).where(LocalBook.filepath == full_path)
                        res_exists = await session.execute(stmt_exists)
                        if res_exists.scalar_one_or_none():
                            continue

                # Procesar libro por EpubScanner (async)
                book_res = await EpubScanner.process_book(
                    full_path,
                    source,
                    session,
                    force_scan,
                    series_provider=SeriesScanner.get_or_create_series,
                    translator_provider=LibraryScanner.sync_translator_group,
                )

                if book_res in ("added", "updated"):
                    stmt_book = select(LocalBook).where(LocalBook.filepath == full_path)
                    res_book = await session.execute(stmt_book)
                    book = res_book.scalar_one_or_none()

                    if book and book.series_hash:
                        results["touched_series_hashes"].add(book.series_hash)
                        if book_res == "added":
                            results["added"] += 1

                            # Better use relation if available
                            results["added_books_details"].append(
                                {
                                    "title": book.title,
                                    "series": book.series_info.series_name if book.series_info else "Unknown",
                                    "volume": book.volume,
                                    "author": book.series_info.author if book.series_info else "Unknown",
                                }
                            )
                        else:
                            results["updated"] += 1
                elif book_res == "duplicate":
                    results["duplicates"] += 1
                elif book_res is False:
                    results["failed"] += 1

                if (results["added"] + results["updated"]) % 50 == 0:
                    await session.commit()

                ScannerService._current_progress["scanned"] = results["total_scanned"]
                await asyncio.sleep(0.01)  # Ceder control para no bloquear main loop

        # Sincronizar metadata de series tocadas
        for h in results["touched_series_hashes"]:
            await SeriesScanner.sync_series_metadata(session, h)

        await session.commit()
        return results, found_files

    async def sync_path(self, path: str, source_id: int = 1, force_scan: bool = True):
        """Sincroniza una ruta específica."""
        # Si ya se está escaneando, podemos intentar procesar esta ruta puntual de todos modos
        # si no es un escaneo masivo. Pero para simplificar, usaremos un lock o permitiremos concurrencia
        # mínima para uploads.
        
        abs_path = os.path.abspath(path).replace("\\", "/")
        if not os.path.exists(abs_path):
            logger.warning(f"Ruta no encontrada para sincronización: {abs_path}")
            return None

        # Si ya hay un escaneo en curso, avisamos pero procedemos si es para un solo archivo puntual
        # para no bloquear uploads críticos.
        is_already_scanning = ScannerService._is_scanning
        if not is_already_scanning:
            ScannerService._is_scanning = True
            
        try:
            async with pg_manager.get_session() as session:
                stmt_source = select(LibrarySource).where(LibrarySource.id == source_id)
                res_source = await session.execute(stmt_source)
                source = (
                    res_source.scalar_one_or_none()
                    or (await session.execute(select(LibrarySource))).scalar_one_or_none()
                )

                if not source:
                    logger.warning(f"No se encontró fuente de librería para id {source_id}")
                    return None

                if os.path.isfile(abs_path) and abs_path.lower().endswith(".epub"):
                    res = await EpubScanner.process_book(
                        abs_path,
                        source,
                        session,
                        force_scan,
                        series_provider=SeriesScanner.get_or_create_series,
                        translator_provider=LibraryScanner.sync_translator_group,
                    )
                    if res in ("added", "updated"):
                        stmt_book = select(LocalBook).where(LocalBook.filepath == abs_path)
                        res_book = await session.execute(stmt_book)
                        book = res_book.scalar_one_or_none()
                        
                        if book and book.series_hash:
                            await SeriesScanner.sync_series_metadata(session, book.series_hash)
                        
                        await session.commit()
                        
                        if book:
                            return {"added": res == "added", "updated": res == "updated", "book_id": book.id}
                        return {"added": res == "added", "updated": res == "updated"}
                    
                    return {"added": False, "updated": False, "status": res}
                else:
                    results, _ = await self._scan_directory(source, session, force_scan)
                    return results
        finally:
            if not is_already_scanning:
                ScannerService._is_scanning = False

    async def sync_series(self, series_hash, force_scan=False):
        """Sincroniza una serie específica."""
        if ScannerService._is_scanning:
            return False

        ScannerService._is_scanning = True
        try:
            async with pg_manager.get_session() as session:
                stmt_books = select(LocalBook).where(LocalBook.series_hash == series_hash)
                res_books = await session.execute(stmt_books)
                books = res_books.scalars().all()
                if not books:
                    return {"success": False}

                dirs = {
                    os.path.dirname(b.filepath)
                    for b in books
                    if b.filepath and os.path.exists(os.path.dirname(b.filepath))
                }
                results = {"added": 0, "updated": 0, "total_scanned": 0}

                source_stmt = select(LibrarySource).where(LibrarySource.id == books[0].source_id)
                source_res = await session.execute(source_stmt)
                source = source_res.scalar_one_or_none()

                for d_path in dirs:
                    for root, _, files in os.walk(d_path):
                        for file in files:
                            if file.lower().endswith(".epub"):
                                full_path = os.path.join(root, file)
                                res = await EpubScanner.process_book(full_path, source, session, force_scan)
                                if res == "added":
                                    results["added"] += 1
                                elif res == "updated":
                                    results["updated"] += 1
                                results["total_scanned"] += 1

                await SeriesScanner.sync_series_metadata(session, series_hash)
                await session.commit()
                return results
        finally:
            ScannerService._is_scanning = False

    @staticmethod
    async def cleanup_library_orphans(session: Any, user_id=None):
        return await LibraryScanner.cleanup_library_orphans(session, user_id)

    async def enrich_all_metadata(self, delay_seconds=2.0):
        return await MaintenanceOrchestrator.run_tool("metadata_enrich", delay_seconds=delay_seconds)

    async def update_all_covers(self):
        return await MaintenanceOrchestrator.run_tool("cover_refresh")

    @classmethod
    def stop_scan(cls):
        if cls._is_scanning:
            cls._stop_requested = True
            logger.info("Solicitud de detención de escaneo recibida.")
            return True
        return False
