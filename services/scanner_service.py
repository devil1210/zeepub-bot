import asyncio
import json
import logging
import os
from datetime import datetime

from sqlalchemy import text

from models.library_models import (
    LibrarySource,
    LocalBook,
)
from services.maintenance.orchestrator import MaintenanceOrchestrator
from services.notification_service import notification_service

# Importar sub-scanners
from services.scanner.epub_scanner import EpubScanner
from services.scanner.library_scanner import LibraryScanner
from services.scanner.series_scanner import SeriesScanner
from utils.library_db import get_session, session_factory

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Servicio de Fachada (Facade) que orquestra la sincronización de la librería.
    Delega las tareas técnicas a módulos especializados en services/scanner/.
    """

    _scan_lock = asyncio.Lock()
    _is_scanning = False
    _stop_requested = False
    _current_progress = {
        "status": "idle",
        "scanned": 0,
        "total": 0,
        "current_source": "",
        "results": {},
        "start_time": None,
        "last_run": None,
        "error_message": None,
    }

    def __init__(self, libraries_config_json: str):
        try:
            self.libraries = json.loads(libraries_config_json)
        except Exception as e:
            logger.error(f"Error parseando configuración de librerías: {e}")
            self.libraries = {}

    async def sync_all(self, force_scan=False, soft_scan=False):
        """Sincroniza todas las fuentes configuradas."""
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso.")
            return False

        ScannerService._is_scanning = True
        ScannerService._stop_requested = False
        ScannerService._current_progress.update(
            {
                "status": "scanning",
                "scanned": 0,
                "total": 0,
                "current_source": "Iniciando...",
                "results": {},
                "start_time": datetime.utcnow().isoformat(),
                "error_message": None,
            }
        )

        # Usar session_factory directamente para evitar conflictos de scoped_session en segundo plano
        session = session_factory()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "removed": 0,
                "archived": 0,
                "sources_scanned": 0,
                "touched_series_hashes": set(),
            }

            local_libs_map = (
                self.libraries if self.libraries else {s.name: s.path for s in session.query(LibrarySource).all()}
            )
            results["sources_scanned"] = len(local_libs_map)
            all_new_books = []

            for name, path in local_libs_map.items():
                if ScannerService._stop_requested:
                    logger.info("Escaneo detenido por el usuario.")
                    break

                ScannerService._current_progress["current_source"] = name
                source = session.query(LibrarySource).filter_by(path=path).first()
                if not source:
                    source = LibrarySource(name=name, path=path)
                    session.add(source)
                    session.commit()

                source_results, found_files = await self._scan_directory(source, session, force_scan, soft_scan)

                if "added_books_details" in source_results:
                    all_new_books.extend(source_results["added_books_details"])

                # Acumular resultados
                for k, v in source_results.items():
                    if k == "touched_series_hashes":
                        results[k].update(v)
                    elif isinstance(v, (int, float)):
                        results[k] = results.get(k, 0) + v

                # Pruning (Detección de archivos eliminados físicamente)
                if not soft_scan:
                    archived, removed = await LibraryScanner.prune_source(session, source, found_files)
                    results["archived"] += archived
                    results["removed"] += removed
                    source.last_scanned = datetime.utcnow()
                    session.commit()

            # Orphan Check (Libros de fuentes no escaneadas)
            if results["sources_scanned"] > 0:
                scanned_ids = [
                    s.id
                    for s in session.query(LibrarySource).filter(LibrarySource.path.in_(local_libs_map.values())).all()
                ]
                detected, moved = LibraryScanner.resolve_orphans(session, scanned_ids)
                results["removed"] += detected

            # AI Gardener
            if results["touched_series_hashes"]:
                await SeriesScanner.run_ai_gardener(session, results["touched_series_hashes"])

            # Sync Book Counts for all series
            session.execute(
                text(
                    "UPDATE series_metadata sm SET book_count = (SELECT COUNT(*) FROM local_books lb WHERE lb.series_hash = sm.series_hash)"
                )
            )
            session.commit()

            # Notificar nuevos libros
            if all_new_books:
                asyncio.create_task(notification_service.notify_new_books(all_new_books))

            # 🛠️ AUTO-HEAL: Corregir integridad y slugs automáticamente
            logger.info("🛠️ Ejecutando auto-correcciones de integridad y slugs...")
            await MaintenanceOrchestrator.run_tool("db_integrity")
            await MaintenanceOrchestrator.run_tool("slug_recalculate")

            if ScannerService._stop_requested:
                ScannerService._current_progress.update(
                    {
                        "status": "cancelled",
                        "results": results,
                        "last_run": datetime.utcnow().isoformat(),
                    }
                )
                logger.info("Escaneo finalizado prematuramente (detenido).")
            else:
                ScannerService._current_progress.update(
                    {
                        "status": "completed",
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
            session.close()
            ScannerService._is_scanning = False

    async def _scan_directory(self, source, session, force_scan=False, soft_scan=False) -> tuple:
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

        import os

        for root, _, files in os.walk(source.path):
            if ScannerService._stop_requested:
                break

            for file in files:
                if ScannerService._stop_requested:
                    break

                if not file.lower().endswith(".epub"):
                    continue

                full_path = os.path.join(root, file)
                found_files.add(full_path)
                results["total_scanned"] += 1

                if soft_scan:
                    mtime = os.path.getmtime(full_path)
                    if (datetime.now() - datetime.fromtimestamp(mtime)).total_seconds() > 86400:
                        if session.query(LocalBook).filter_by(filepath=full_path).exists():
                            continue

                # Delegar al EpubScanner
                book_res = await EpubScanner.process_book(
                    full_path,
                    source,
                    session,
                    force_scan,
                    series_provider=SeriesScanner.get_or_create_series,
                    translator_provider=LibraryScanner.sync_translator_group,
                )

                if book_res in ("added", "updated"):
                    book = session.query(LocalBook).filter_by(filepath=full_path).first()
                    if book and book.series_hash:
                        results["touched_series_hashes"].add(book.series_hash)
                        if book_res == "added":
                            results["added"] += 1
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
                    session.commit()

                ScannerService._current_progress["scanned"] = results["total_scanned"]
                await asyncio.sleep(0)

        # Sync metadata for touched series
        for h in results["touched_series_hashes"]:
            SeriesScanner.sync_series_metadata(session, h)

        session.commit()
        return results, found_files

    async def sync_path(self, path: str, source_id: int = 1, force_scan: bool = True):
        """Sincroniza una ruta específica."""
        if ScannerService._is_scanning:
            return None
        ScannerService._is_scanning = True
        session = get_session()
        try:
            source = session.query(LibrarySource).get(source_id) or session.query(LibrarySource).first()
            if not source:
                return None

            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
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
                    book = session.query(LocalBook).filter_by(filepath=abs_path).first()
                    if book and book.series_hash:
                        SeriesScanner.sync_series_metadata(session, book.series_hash)
                session.commit()
                return {"added": 1 if res == "added" else 0, "updated": 1 if res == "updated" else 0}
            else:
                results, _ = await self._scan_directory(source, session, force_scan)
                return results
        finally:
            session.close()
            ScannerService._is_scanning = False

    async def sync_series(self, series_hash, force_scan=False):
        """Sincroniza una serie específica."""
        if ScannerService._is_scanning:
            return False
        ScannerService._is_scanning = True
        session = get_session()
        try:
            books = session.query(LocalBook).filter_by(series_hash=series_hash).all()
            if not books:
                return {"success": False}

            dirs = {
                os.path.dirname(b.filepath) for b in books if b.filepath and os.path.exists(os.path.dirname(b.filepath))
            }
            results = {"added": 0, "updated": 0, "total_scanned": 0}

            for d_path in dirs:
                source = session.query(LibrarySource).filter_by(id=books[0].source_id).first()
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

            SeriesScanner.sync_series_metadata(session, series_hash)
            session.commit()
            return results
        finally:
            session.close()
            ScannerService._is_scanning = False

    @staticmethod
    def sync_series_metadata(session, series_hash: str):
        """Método estático de compatibilidad."""
        SeriesScanner.sync_series_metadata(session, series_hash)

    @staticmethod
    async def cleanup_library_orphans(session, user_id=None):
        """Método estático de compatibilidad."""
        return await LibraryScanner.cleanup_library_orphans(session, user_id)

    async def enrich_all_metadata(self, delay_seconds=2.0):
        """Busca metadatos online para libros que tienen ISBN."""
        return await MaintenanceOrchestrator.run_tool("metadata_enrich", delay_seconds=delay_seconds)

    async def update_all_covers(self):
        """Refresca las portadas de todos los libros en la biblioteca."""
        return await MaintenanceOrchestrator.run_tool("cover_refresh")

    @classmethod
    def stop_scan(cls):
        """Solicita detener el escaneo actual."""
        if cls._is_scanning:
            cls._stop_requested = True
            logger.info("Solicitud de detención de escaneo recibida.")
            return True
        return False
