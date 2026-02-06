import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime

from sqlalchemy import func, select

from models.library_models import (
    ArchivedBook,
    ArchivedSeries,
    DuplicateBook,
    LibrarySource,
    LocalBook,
    MetadataProposal,
    SeriesMetadata,
)
from services.ai_service import AIService
from services.hash_service import hash_service
from utils.epub_extractor import EpubMetadataExtractor
from utils.library_db import COVERS_DIR, get_session

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Servicio encargado de sincronizar las carpetas físicas con la base de datos.
    """

    _scan_lock = asyncio.Lock()
    _is_scanning = False
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

    # Géneros que son "rasgos" de edición y deben bueblear a la serie si algún volumen los tiene
    TRAIT_TAGS = {
        "Sin Censura",
        "Ilustraciones a Color",
        "Mature",
        "One-shot",
        "Spin-off",
        "Anthology",
    }

    def __init__(self, libraries_config_json: str):
        """
        libraries_config_json: JSON string con formato '{"Nombre": "/ruta", ...}'
        """
        try:
            self.libraries = json.loads(libraries_config_json)
        except Exception as e:
            logger.error(f"Error parseando configuración de librerías: {e}")
            self.libraries = {}

    async def sync_all(self, force_scan=False, soft_scan=False):
        """
        Sincroniza todas las fuentes configuradas.
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso. Saltando.")
            return False

        ScannerService._is_scanning = True
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
        session = get_session()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "removed": 0,
                "archived": 0,
                "covers_created": 0,
                "sources_scanned": len(self.libraries),
                "touched_series_hashes": set(),
            }

            # Si self.libraries está vacío (caso común al iniciar sin config env),
            # cargamos TODAS las fuentes desde la base de datos para escanear todo.
            if not self.libraries:
                all_sources = session.query(LibrarySource).all()
                local_libs_map = {s.name: s.path for s in all_sources}
            else:
                # Si se pasaron librerías específicas, usamos esas
                local_libs_map = self.libraries

            results["sources_scanned"] = len(local_libs_map)

            for name, path in local_libs_map.items():
                ScannerService._current_progress["current_source"] = name
                logger.info(f"Iniciando escaneo de fuente: {name} ({path})")

                # 1. Asegurar que la fuente existe en DB (si viene del JSON)
                source = session.query(LibrarySource).filter_by(path=path).first()
                if not source:
                    source = LibrarySource(name=name, path=path)
                    session.add(source)
                    session.commit()

                source_results, found_files = await self._scan_directory(
                    source, session, force_scan, soft_scan
                )

                # Update global results
                for k, v in source_results.items():
                    if k == "touched_series_hashes":
                        results[k].update(v)
                    elif isinstance(v, (int, float)):
                        results[k] = results.get(k, 0) + v
                    else:
                        results[k] = v

                # --- PRUNING: Delete books in DB not found on disk ---
                # Saltamos pruning en escaneo suave para máxima velocidad
                if soft_scan:
                    logger.info(f"Escaneo suave activado para {name}. Saltando pruning.")
                else:
                    try:
                        # Get all DB filepaths for this source
                        db_books = (
                            session.query(LocalBook.filepath)
                            .filter(LocalBook.source_id == source.id)
                            .all()
                        )
                        db_paths = {b[0] for b in db_books}

                        missing_paths = db_paths - found_files
                        if missing_paths:
                            logger.info(
                                f"Detectados {len(missing_paths)} libros eliminados físicamente. Archivando en DB..."
                            )

                            missing_list = list(missing_paths)
                            chunk_size = 500
                            affected_series_hashes = set()

                            for i in range(0, len(missing_list), chunk_size):
                                chunk = missing_list[i : i + chunk_size]

                                # 1. Obtener objetos completos para archivar
                                books_to_archive = (
                                    session.query(LocalBook)
                                    .filter(LocalBook.filepath.in_(chunk))
                                    .all()
                                )

                                for b in books_to_archive:
                                    if b.series_hash:
                                        affected_series_hashes.add(b.series_hash)

                                    # Crear registro de archivo
                                    archived = ArchivedBook(
                                        series_hash=b.series_hash,
                                        book_hash=b.book_hash,
                                        title=b.title,
                                        filename=b.filename,
                                        last_filepath=b.filepath,
                                        volume=b.volume,
                                        author=b.author,
                                        book_type=b.book_type,
                                        original_book_id=b.id,
                                        reason="physically_deleted",
                                    )
                                    session.add(archived)
                                    results["archived"] = results.get("archived", 0) + 1

                                # 1.1 Desvincular de tablas históricas para evitar ForeignKeyViolation
                                from models.download_models import DownloadHistory
                                from models.library_models import UserDownload, UserRating

                                book_ids = [b.id for b in books_to_archive]
                                if book_ids:
                                    session.query(DownloadHistory).filter(
                                        DownloadHistory.book_id.in_(book_ids)
                                    ).update(
                                        {DownloadHistory.book_id: None}, synchronize_session=False
                                    )

                                    session.query(UserDownload).filter(
                                        UserDownload.book_id.in_(book_ids)
                                    ).update(
                                        {UserDownload.book_id: None}, synchronize_session=False
                                    )

                                    session.query(UserRating).filter(
                                        UserRating.book_id.in_(book_ids)
                                    ).update({UserRating.book_id: None}, synchronize_session=False)

                                # 2. Eliminar de la tabla principal
                                session.query(LocalBook).filter(
                                    LocalBook.filepath.in_(chunk)
                                ).delete(synchronize_session=False)
                                session.commit()  # Commit chunks to keep memory clean

                                # Ceder control
                                await asyncio.sleep(0)

                            # 3. Verificar series huérfanas
                            for s_hash in affected_series_hashes:
                                # Contar si quedan libros en LocalBook para esta serie
                                count = (
                                    session.query(LocalBook).filter_by(series_hash=s_hash).count()
                                )
                                if count == 0:
                                    # Archivar serie
                                    series = (
                                        session.query(SeriesMetadata)
                                        .filter_by(series_hash=s_hash)
                                        .first()
                                    )
                                    if series:
                                        logger.info(
                                            f"Archivando serie completa por falta de volúmenes: {series.series_name}"
                                        )
                                        archived_s = ArchivedSeries(
                                            series_name=series.series_name,
                                            series_spanish=series.series_spanish,
                                            series_hash=series.series_hash,
                                            author=series.author,
                                            description=series.description,
                                            tags=series.tags,
                                            cover_url=series.cover_url,
                                            book_type=series.book_type,
                                            publisher=series.publisher,
                                            original_series_id=series.id,
                                        )
                                        session.add(archived_s)
                                        session.delete(series)
                                        results["archived"] = results.get("archived", 0) + 1
                                        session.commit()

                            results["removed"] = results.get("removed", 0) + len(missing_paths)
                    except Exception as e:
                        logger.error(f"Error durante pruning de {name}: {e}")
                        session.rollback()

                if not soft_scan:
                    source.last_scanned = datetime.utcnow()
                    session.commit()

                session.commit()

            # --- ORPHAN CHECK ---
            # Verificar si hay libros en la DB que pertenecen a fuentes que NO se han escaneado en esta ejecución.
            # Esto explica discrepancias entre Total Index y Libros Escaneados.
            if results["sources_scanned"] > 0:
                scanned_source_ids = [
                    s.id
                    for s in session.query(LibrarySource)
                    .filter(LibrarySource.path.in_(local_libs_map.values()))
                    .all()
                ]
                if scanned_source_ids:
                    # Get orphans instead of just counting
                    orphans_q = session.query(LocalBook).filter(
                        LocalBook.source_id.notin_(scanned_source_ids)
                    )
                    orphans_list = orphans_q.all()

                    if orphans_list:
                        logger.warning(
                            f"⚠️ ALERTA DE ORDANDAD: {len(orphans_list)} libros huérfanos detectados. Moviendo a tabla de Duplicados para revisión."
                        )

                        count_moved = 0
                        affected_hashes = set()
                        for orphan in orphans_list:
                            if orphan.series_hash:
                                affected_hashes.add(orphan.series_hash)

                            # Verify if already in duplicates to avoid spam
                            exists = (
                                session.query(DuplicateBook)
                                .filter_by(duplicate_filepath=orphan.filepath)
                                .first()
                            )
                            if not exists:
                                dup = DuplicateBook(
                                    book_hash=orphan.book_hash,
                                    original_filepath="ORPHAN_RECORD",  # Marker for frontend/admin
                                    duplicate_filepath=orphan.filepath,
                                    title=f"[HUÉRFANO] {orphan.title}",
                                    author=orphan.author,
                                )
                                session.add(dup)
                                count_moved += 1

                            # BORRAR de local_books siempre (quedará en ArchivedBook si queremos, o simplemente desaparece de la vista activa)
                            session.delete(orphan)

                        if count_moved > 0 or len(orphans_list) > 0:
                            session.commit()

                            # Sincronizar metadata para series que perdieron libros huérfanos
                            for h in affected_hashes:
                                self.sync_series_metadata(session, h)
                            session.commit()

                        results["orphans_detected"] = len(orphans_list)
                        results["orphans_moved_to_duplicates"] = count_moved
                        results["removed"] = results.get("removed", 0) + len(orphans_list)

                        if "touched_series_hashes" not in results:
                            results["touched_series_hashes"] = set()
                        results["touched_series_hashes"].update(affected_hashes)

            # --- AI PROPOSALS (Background Gardener) ---
            # Si hubo cambios o es un escaneo completo, generar propuestas para series 'tocadas'
            # Y si está activado el modo background, buscar otras series candidatas (Jardinero)
            touched_hashes = results.get("touched_series_hashes", set())

            # Check user setting
            from services.settings_service import get_setting

            bg_ai_enabled = get_setting("enable_background_ai_scan", "false").lower() == "true"

            if bg_ai_enabled:
                try:
                    candidates = list(touched_hashes)
                    SCAN_LIMIT = 5  # Max proposals per scan cycle to avoid rate limits

                    # Si tenemos espacio, buscar en el backlog (series con libros pero sin feedback ni propuestas)
                    if len(candidates) < SCAN_LIMIT:
                        needed = SCAN_LIMIT - len(candidates)
                        # Query compleja: Series con > 2 libros, sin feedback, sin propuestas pendientes
                        # SQL Raw para eficiencia
                        from sqlalchemy import text

                        backlog_query = text("""
                            SELECT lb.series_hash
                            FROM local_books lb
                            WHERE lb.series_hash NOT IN (SELECT series_hash FROM ai_learning_feedback)
                              AND lb.series_hash NOT IN (SELECT series_hash FROM metadata_proposals WHERE status='pending')
                              AND lb.series_hash IS NOT NULL
                            GROUP BY lb.series_hash
                            HAVING COUNT(*) >= 2
                            LIMIT :limit
                        """)
                        res = session.execute(backlog_query, {"limit": needed})
                        for row in res:
                            candidates.append(row[0])

                    processed_count = 0
                    logger.info(
                        f"AI Gardener: Procesando {len(candidates)} candidatos (Limit: {SCAN_LIMIT})..."
                    )

                    for s_hash in candidates:
                        if processed_count >= SCAN_LIMIT:
                            break

                        # Solo si no tiene propuesta pendiente Y no ha sido revisada recientemente (feedback)
                        exists_pending = (
                            session.query(MetadataProposal)
                            .filter_by(series_hash=s_hash, status="pending")
                            .first()
                        )

                        # Check if already reviewed in learning feedback (Double check for touched ones)
                        reviewed = session.execute(
                            text(
                                "SELECT 1 FROM ai_learning_feedback WHERE series_hash = :h LIMIT 1"
                            ),
                            {"h": s_hash},
                        ).first()

                        if not exists_pending and not reviewed:
                            current_s = (
                                session.query(SeriesMetadata).filter_by(series_hash=s_hash).first()
                            )
                            current_name = (
                                current_s.series_name if current_s else "Serie Desconocida"
                            )

                            series_books = (
                                session.query(LocalBook).filter_by(series_hash=s_hash).all()
                            )
                            # Relaxed constraint for backlog items, but keep sanity
                            if series_books:
                                try:
                                    logger.info(f"AI Analysis: {s_hash[:8]} - {current_name}")
                                    proposal = await AIService.analyze_series_for_updates(
                                        s_hash,
                                        current_name,
                                        [b.to_dict() for b in series_books],
                                        current_s.series_spanish if current_s else None,
                                    )
                                    processed_count += 1
                                except Exception as ae:
                                    logger.warning(
                                        f"Error generando propuesta IA para {s_hash}: {ae}"
                                    )
                                    proposal = None

                                if proposal:
                                    p_obj = MetadataProposal(
                                        series_hash=s_hash,
                                        proposal_data=proposal,
                                        status="pending",
                                    )
                                    session.add(p_obj)
                                    session.commit()  # Commit per proposal
                except Exception as ae:
                    logger.warning(f"Error generando propuestas IA en segundo plano: {ae}")

            # --- FINAL CLEANUP: Remove/Archive empty series ---
            try:
                # FORCE REFRESH: Recalculate book_count for ALL non-archived series to fix stale data
                logger.info("Sincronizando conteos de libros para todas las series...")
                all_active_series = session.query(SeriesMetadata).all()
                for i, s in enumerate(all_active_series):
                    actual_count = (
                        session.query(LocalBook).filter_by(series_hash=s.series_hash).count()
                    )
                    if s.book_count != actual_count:
                        s.book_count = actual_count
                    if i % 20 == 0:
                        await asyncio.sleep(0)
                session.commit()

                empty_series = (
                    session.query(SeriesMetadata).filter(SeriesMetadata.book_count == 0).all()
                )
                if empty_series:
                    logger.info(f"Limpieza final: Archivando {len(empty_series)} series vacías...")
                    for s in empty_series:
                        archived_s = ArchivedSeries(
                            series_name=s.series_name,
                            series_spanish=s.series_spanish,
                            series_hash=s.series_hash,
                            author=s.author,
                            description=s.description,
                            tags=s.tags,
                            cover_url=s.cover_url,
                            book_type=s.book_type,
                            publisher=s.publisher,
                            original_series_id=s.id,
                        )
                        session.add(archived_s)
                        session.delete(s)
                        results["archived"] = results.get("archived", 0) + 1
                    session.commit()
            except Exception as ce:
                logger.warning(f"Error en limpieza final de series: {ce}")

            logger.info(f"Escaneo completado: {results}")
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
            # No resetear a 'idle' si terminó con éxito o error para que el usuario vea el log

    async def sync_path(self, path: str, source_id: int = 1, force_scan: bool = True):
        """
        Sincroniza una ruta específica (archivo o directorio).
        Útil para procesar inmediatamente archivos recién subidos.
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso. Saltando sync_path.")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "covers_created": 0,
            }

            source = session.query(LibrarySource).get(source_id)
            if not source:
                source = session.query(LibrarySource).first()

            if not source:
                logger.error("No se encontró ninguna fuente de librería válida.")
                return None

            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                logger.error(f"La ruta no existe: {abs_path}")
                return None

            if os.path.isfile(abs_path):
                # Es un archivo individual
                if abs_path.lower().endswith(".epub"):
                    results["total_scanned"] = 1
                    res, s_hash = await self._process_book_with_hash(
                        abs_path, source, session, force_scan
                    )
                    if res == "added":
                        results["added"] = 1
                    elif res == "updated":
                        results["updated"] = 1
                    elif res == "duplicate":
                        results["duplicates"] = 1
                    elif res is False:
                        results["failed"] = 1

                    if s_hash:
                        self.sync_series_metadata(session, s_hash)
            else:
                # Es un directorio
                source_results, _ = await self._scan_directory(source, session, force_scan)
                results.update(source_results)

            session.commit()
            logger.info(f"Escaneo de ruta {path} completado: {results}")
            return results
        except Exception as e:
            logger.error(f"Error en sync_path: {e}")
            session.rollback()
            return None
        finally:
            session.close()
            ScannerService._is_scanning = False

    async def sync_series(self, series_hash, force_scan=False):
        """
        Sincroniza una serie específica basada en su hash.
        Busca los libros que pertenecen a esa serie y los re-procesa.
        También escanea las carpetas donde se encuentran esos libros por si hay nuevos.
        """
        if ScannerService._is_scanning:
            logger.warning("Ya hay un escaneo en curso. Saltando.")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            results = {
                "total_scanned": 0,
                "added": 0,
                "updated": 0,
                "duplicates": 0,
                "failed": 0,
                "covers_created": 0,
            }

            # 1. Obtener libros existentes de esta serie para saber en qué carpetas buscar
            books = session.query(LocalBook).filter_by(series_hash=series_hash).all()
            if not books:
                logger.warning(f"No se encontraron libros para la serie con hash: {series_hash}")
                return {
                    "success": False,
                    "message": "Serie no encontrada en la base de datos local.",
                }

            # 2. Identificar las carpetas (directorios) a escanear
            # Generalmente una serie está en una única carpeta, pero podría estar dispersa.
            directories_to_scan = set()
            source_map = {}  # path -> source_id

            for b in books:
                dir_path = os.path.dirname(b.filepath)
                if os.path.exists(dir_path):
                    directories_to_scan.add(dir_path)
                    source_map[dir_path] = b.source_id

            logger.info(
                f"Sincronizando serie {series_hash}. Directorios a escanear: {len(directories_to_scan)}"
            )

            # 3. Escanear cada directorio encontrado
            for dir_path in directories_to_scan:
                source_id = source_map[dir_path]
                source = session.query(LibrarySource).get(source_id)
                if not source:
                    continue

                # Escaneamos solo el directorio específico (no recursivo hacia arriba, pero os.walk es recursivo hacia abajo)
                # En muchos casos el directorio de la serie es el final, pero si hay subcarpetas las procesará.
                for root, _dirs, files in os.walk(dir_path):
                    for file in files:
                        if file.lower().endswith(".epub"):
                            results["total_scanned"] += 1
                            full_path = os.path.join(root, file)

                            # Procesar el libro
                            book_result, s_hash = await self._process_book_with_hash(
                                full_path, source, session, force_scan
                            )

                            if book_result == "added":
                                results["added"] += 1
                            elif book_result == "updated":
                                results["updated"] += 1
                            elif book_result == "duplicate":
                                results["duplicates"] += 1
                            elif book_result is False:
                                results["failed"] += 1

                # Re-sincronizar esta serie específicamente
                self.sync_series_metadata(session, series_hash)
                session.commit()

            logger.info(f"Sincronización de serie {series_hash} completada: {results}")
            return results
        except Exception as e:
            logger.error(f"Error en sync_series: {e}")
            session.rollback()
            return None
        finally:
            session.close()
            ScannerService._is_scanning = False

    async def _scan_directory(self, source, session, force_scan=False, soft_scan=False):
        """
        Recorre el directorio y procesa archivos nuevos o modificados.
        """
        results = {
            "total_scanned": 0,
            "added": 0,
            "updated": 0,
            "duplicates": 0,
            "failed": 0,
            "covers_created": 0,
        }

        found_files = set()
        touched_hashes = set()
        for root, _dirs, files in os.walk(source.path):
            for file in files:
                if file.lower().endswith(".epub"):
                    results["total_scanned"] += 1
                    full_path = os.path.join(root, file)
                    found_files.add(full_path)

                    # Escaneo suave: Solo archivos modificados en las últimas 24 horas
                    if soft_scan:
                        try:
                            mtime = os.path.getmtime(full_path)
                            mod_time = datetime.fromtimestamp(mtime)
                            if (datetime.now() - mod_time).total_seconds() > 86400:
                                # Opcional: Si el archivo es nuevo no registrado, igual procesarlo.
                                # Pero por ahora, el usuario pide estrictamente "cambiados en el último día".
                                # Para mayor seguridad, si no está en la DB, lo procesamos.
                                exists_in_db = (
                                    session.query(LocalBook).filter_by(filepath=full_path).first()
                                )
                                if exists_in_db:
                                    continue
                        except Exception:
                            pass

                    # El tercer valor retornado por _process_book será el series_hash si se procesó
                    book_res, s_hash = await self._process_book_with_hash(
                        full_path, source, session, force_scan
                    )
                    if s_hash:
                        touched_hashes.add(s_hash)

                    if book_res == "added":
                        results["added"] += 1
                    elif book_res == "updated":
                        results["updated"] += 1
                    elif book_res == "duplicate":
                        results["duplicates"] += 1
                    elif book_res is False:
                        results["failed"] += 1

                    if book_res in ("added", "updated"):
                        if "touched_series_hashes" not in results:
                            results["touched_series_hashes"] = set()
                        if s_hash:
                            results["touched_series_hashes"].add(s_hash)

                    # Batch commit para no bloquear DB mucho tiempo pero asegurar progreso
                    if (results["added"] + results["updated"]) % 50 == 0 and (
                        results["added"] + results["updated"]
                    ) > 0:
                        session.commit()
                        logger.info(
                            f"Progreso de escaneo: {results['added'] + results['updated']} libros procesados en {source.name}"
                        )

                # Update progress
                ScannerService._current_progress["scanned"] = results["total_scanned"]
                # Ceder el control al event loop en cada archivo (sea epub o no) para máxima respuesta
                await asyncio.sleep(0)

        # Sincronizar metadata de todas las series tocadas en esta fuente
        for i, h in enumerate(touched_hashes):
            self.sync_series_metadata(session, h)
            if i % 10 == 0:
                await asyncio.sleep(0)

        session.commit()

        return results, found_files

    def _get_or_create_series(self, session, book: LocalBook) -> SeriesMetadata:
        """
        Obtiene o crea una entrada en SeriesMetadata para el libro.
        Normaliza campos comunes de la serie.
        """
        series = session.query(SeriesMetadata).filter_by(series_hash=book.series_hash).first()

        if not series:
            series = SeriesMetadata(
                series_name=book.series or book.title,
                series_spanish=book.series_spanish,
                series_hash=book.series_hash,
                author=book.author,
                author_jap=book.author_jap,
                description=book.description,
                tags=book.tags or [],
                book_type=book.book_type,
                publisher=book.publisher,
                cover_url=book.cover_low or book.cover_medium,
                book_count=0,
            )
            session.add(series)
            session.flush()  # Para obtener el ID
            logger.info(f"🆕 Nueva serie detectada: {series.series_name}")
        else:
            # Sincronizar campos: Actualizar si el libro tiene info y es distinta o la serie está vacía
            if book.author and series.author != book.author:
                series.author = book.author

            if book.description and (
                not series.description or len(book.description) > len(series.description)
            ):
                series.description = book.description

            # UNIÓN DE TAGS: La serie tiene todos los géneros que tengan sus volúmenes
            if book.tags:
                existing_tags = set(series.tags) if series.tags else set()
                new_tags = set(book.tags)
                if not new_tags.issubset(existing_tags):
                    series.tags = list(existing_tags | new_tags)
                    logger.info(f"🏷️ Tags de serie actualizados (Unión): {series.series_name}")

            if book.series_spanish and series.series_spanish != book.series_spanish:
                series.series_spanish = book.series_spanish

            if book.book_type and series.book_type != book.book_type:
                series.book_type = book.book_type

            if book.publisher and series.publisher != book.publisher:
                series.publisher = book.publisher

            # PORTADA: Usar la del volumen 1 (o el más bajo disponible)
            if book.cover_low or book.cover_medium:
                # Si es el volumen 1 o no tenemos portada aún, actualizarla
                if book.volume == 1 or not series.cover_url:
                    series.cover_url = book.cover_low or book.cover_medium

        return series

    async def _process_book_with_hash(self, filepath, source, session, force_scan=False):
        """Wrapper de _process_book que también devuelve el hash de la serie."""
        res = await self._process_book(filepath, source, session, force_scan)
        # Buscar el hash en la DB tras el procesamiento
        if res in ("added", "updated", "skipped"):
            book = session.query(LocalBook).filter_by(filepath=filepath).first()
            if book:
                return res, book.series_hash
        return res, None

    async def _process_book(self, filepath, source, session, force_scan=False) -> bool:
        """
        Procesa un archivo individual. Devuelve True si el libro fue procesado/actualizado.
        """
        try:
            stat = os.stat(filepath)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size

            # Buscar si ya existe en DB
            book = session.query(LocalBook).filter_by(filepath=filepath).first()

            # Si ya existe y no ha cambiado el mtime ni el tamaño, saltar (a menos que sea force_scan)
            # SI el libro existe pero no tiene metadata enriquecida (word_count es 0 o None),
            # forzamos el procesamiento de metadata técnica
            force_metadata = False
            filename = os.path.basename(filepath)

            # Verificar si las portadas existen físicamente en el disco
            missing_covers = False
            if book and book.cover_low:
                from utils.library_db import DB_DIR

                # La ruta guardada es /api/library/covers/filename.jpg
                # Debemos convertirla a ruta local data/library/covers/filename.jpg
                relative_path = book.cover_low.replace("/api/library/covers/", "")
                local_cover_path = os.path.join(DB_DIR, "covers", relative_path)
                if not os.path.exists(local_cover_path):
                    missing_covers = True
                    logger.warning(
                        f"Portada no encontrada en disco para {filename}: {local_cover_path}"
                    )

            if book and (not book.word_count or book.word_count == 0):
                logger.info(f"Forzando extracción de metadata para {filename} (metadata faltante)")
                force_metadata = True

            if (
                not force_scan
                and not force_metadata
                and not missing_covers
                and book
                and book.file_modified_at == mtime
                and book.file_size == size
                and book.book_hash
                and book.cover_low
                and book.series_metadata_id is not None
                and book.series
                and book.author
                and book.volume is not None
                # FORCE UPDATE IF SERIES HASH LOGIC CHANGED (Migration Fix)
                and book.series_hash
                == hash_service.generate_series_hash(book.series, book.author, book.book_type)
            ):
                return "skipped"

            action_type = "Re-procesando" if book else "Procesando"
            if missing_covers:
                action_type = "Recuperando portadas de"
            elif force_scan:
                action_type = "Forzando escaneo de"

            logger.info(f"{action_type}: {filename}")

            # Primero extraer metadatos crudos para campos extendidos (descripción, ISBN, etc)
            extractor = EpubMetadataExtractor(filepath)
            meta = extractor.extract()
            if not meta:
                return

            # --- LÓGICA UNIFICADA DE IDENTIDAD ---
            from utils.helpers import (
                process_book_identity_comprehensive,
            )

            identity = process_book_identity_comprehensive(filepath)
            if not identity:
                return

            if not book:
                book = LocalBook(filepath=filepath, source_id=source.id)

            # Actualizar campos técnicos
            book.filename = os.path.basename(filepath)
            book.file_size = size
            book.file_modified_at = mtime
            book.file_created_at = datetime.fromtimestamp(stat.st_ctime)

            # Poblar desde identidad unificada (Garantiza paridad con Uploader)
            book.title = identity["title"]
            book.author = identity["author"]
            book.series = identity["series"]
            book.volume = identity["volume"]
            book.book_type = identity["book_type"]
            book.language = identity["language"]
            book.translator = identity["translator"]
            book.layout_by = identity["layout_by"]
            book.series_spanish = identity["series_spanish"]
            book.series_english = identity["series_english"]
            book.edition = identity["edition"]

            # Japanese Names
            book.author_jap = meta.get("author_jap")
            book.illustrator_jap = meta.get("illustrator_jap")

            # Campos específicos de metadatos profundos
            book.description = meta.get("description")

            book.illustrator = meta.get("illustrator")
            book.publisher = meta.get("publisher")

            # Tags y Demografía (Lógica adicional del scanner)
            raw_tags = meta.get("tags", [])
            classified_demographics = []
            final_genres = []

            known_demographics = [
                "shounen",
                "seinen",
                "shoujo",
                "josei",
                "kodomo",
                "seijin",
                "adultos",
                "mature",
                "maduro",
            ]
            for tag in raw_tags:
                t_lower = tag.lower().strip()
                if any(d in t_lower for d in known_demographics):
                    classified_demographics.append(tag)
                else:
                    final_genres.append(tag)

            book.demographics = classified_demographics
            book.tags = final_genres

            # Romaji extraction
            romaji = meta.get("romaji_title")
            if not romaji and book.title:
                title_without_vol = re.sub(
                    r"\s*-\s*Volumen\s+\d+.*$", "", book.title, flags=re.IGNORECASE
                ).strip()
                romaji = (
                    title_without_vol.split(" - ")[0].strip()
                    if " - " in title_without_vol
                    else title_without_vol
                )
            book.romaji_title = romaji

            # Enriched identifiers and dates
            book.isbn = meta.get("isbn")
            book.asin = meta.get("asin")
            book.uri_id = meta.get("uri")
            book.published_at = meta.get("published_at")
            book.modified_at_opf = meta.get("modified_at_opf")
            book.epub_version = meta.get("version")
            book.word_count = meta.get("word_count")
            book.page_count = meta.get("page_count")
            book.reading_time = meta.get("reading_time")
            book.is_uncensored = meta.get("is_uncensored", 0)
            book.color_mode = meta.get("color_mode")

            # --- GENERAR HASHES (TEMPORALES) ---
            # Usamos el objeto 'book' como contenedor temporal de metadata
            target_series_hash = self._generate_series_hash(book)
            target_book_hash = self._generate_book_hash(book)

            # Advertencia de tags legacy para unificación
            legacy_tags = ["[BN]", "[COLOR]", "[SC]", "[SIN CENSURA]", "[B&W]"]
            raw_title_full = meta.get("title", "") + " " + " ".join(meta.get("tags", []))
            for lt in legacy_tags:
                if lt in raw_title_full.upper():
                    logger.warning(
                        f"⚠️ Metadata Legacy Detectada: El libro '{book.title}' contiene el tag '{lt}'. Se recomienda mover esta información a los metadatos oficiales (dc:subject) o meta-propiedades zeepub para una unificación completa."
                    )
                    break

            # Check for duplicates and hash conflicts
            # Guardamos la metadata extraída en un objeto temporal si es necesario copiarla luego
            extracted_book_data = book  # 'book' ya tiene la metadata seteada arriba

            with session.no_autoflush:
                existing_same_file = (
                    session.query(LocalBook).filter(LocalBook.filepath == filepath).first()
                )

                if existing_same_file:
                    # Caso 1: El archivo ya existe en la DB (por filepath).
                    # Verificamos si al actualizar la metadata genera un hash que YA tiene OTRO archivo.
                    if existing_same_file.book_hash != target_book_hash:
                        hash_conflict = (
                            session.query(LocalBook)
                            .filter(
                                LocalBook.book_hash == target_book_hash,
                                LocalBook.id != existing_same_file.id,
                            )
                            .first()
                        )

                        if hash_conflict:
                            logger.warning(
                                f"📕 Duplicado detectado por cambio de metadata (Hash Conflict): {book.title} -> {hash_conflict.filepath}"
                            )
                            return "duplicate"

                    # Si no hay conflicto y el archivo ya existía, preservamos sus hashes originales
                    # de metadata (Identidad inmutable) según pedido del usuario.
                    book = existing_same_file
                    if not book.series_hash or force_scan:
                        book.series_hash = target_series_hash
                    if not book.book_hash or force_scan:
                        book.book_hash = target_book_hash

                    # No sobreescribir book.series (Metadata de Identidad) con la corrección IA
                    # si ya existe, a menos que se fuerce.
                    if not book.series or force_scan:
                        book.series = extracted_book_data.series

                    outcome = "updated"
                else:
                    # Caso 2: Nuevo archivo en disco (no encontrado por filepath).
                    # Verificar si existe otro registro con el mismo contenido/hash.
                    existing_with_same_hash = (
                        session.query(LocalBook)
                        .filter(LocalBook.book_hash == target_book_hash)
                        .first()
                    )

                    if existing_with_same_hash:
                        # Conflict detected based on Content Hash.
                        # Check if the "original" file still exists on disk.
                        if not os.path.exists(existing_with_same_hash.filepath):
                            # Migración (Rename/Move): El archivo cambió de sitio pero el contenido es el mismo.
                            logger.info(
                                f"🔄 Migración detectada (Renombrado/Movido): {existing_with_same_hash.filepath} -> {filepath}"
                            )
                            # Actualizamos el registro viejo con la nueva ubicación y la metadata
                            self._copy_metadata_to_existing(
                                extracted_book_data, existing_with_same_hash
                            )

                            book = existing_with_same_hash
                            book.filepath = filepath
                            book.filename = os.path.basename(filepath)
                            book.file_size = size
                            book.file_modified_at = mtime
                            book.source_id = source.id
                            # En migración por renombrado, preservamos IDENTIDAD original (hashes)
                            # pero actualizamos por si acaso si son nulos.
                            if not book.series_hash or force_scan:
                                book.series_hash = target_series_hash
                            if not book.book_hash or force_scan:
                                book.book_hash = target_book_hash

                            outcome = "updated"
                        else:
                            # Duplicado REAL: Dos archivos distintos con el mismo contenido.
                            logger.warning(f"📕 Duplicado detectado: {book.title}")
                            try:
                                dup_exists = (
                                    session.query(DuplicateBook)
                                    .filter_by(duplicate_filepath=filepath)
                                    .first()
                                )
                                if not dup_exists:
                                    dup = DuplicateBook(
                                        book_hash=target_book_hash,
                                        original_filepath=existing_with_same_hash.filepath,
                                        duplicate_filepath=filepath,
                                        title=book.title,
                                        author=book.author,
                                    )
                                    session.add(dup)
                                    session.commit()
                            except Exception as de:
                                logger.error(f"Error registrando duplicado: {de}")
                                session.rollback()
                            return "duplicate"
                    else:
                        # Archivo nuevo y único en todo sentido.
                        book.series_hash = target_series_hash
                        book.book_hash = target_book_hash
                        session.add(book)
                        outcome = "added"

            # --- VINCULACIÓN CON SERIES_METADATA ---
            # Asegurar que el objeto esté en la sesión antes de vincular
            if book not in session:
                session.add(book)

            series = self._get_or_create_series(session, book)
            book.series_metadata_id = series.id

            # --- VINCULACIÓN CON GRUPOS DE TRADUCCIÓN ---
            self._sync_translator_group(session, book)

            # Actualizar conteo de libros en la serie
            count_stmt = select(func.count(LocalBook.id)).where(
                LocalBook.series_hash == series.series_hash
            )
            series.book_count = session.execute(count_stmt).scalar() or 0

            # Guardar Portada en 4 calidades (outside no_autoflush block)
            if extractor.cover_data:
                cover_filename = f"{hashlib.md5(filepath.encode()).hexdigest()}.jpg"
                cover_dest = os.path.join(COVERS_DIR, cover_filename)
                cover_paths = extractor.save_cover(cover_dest)
                if cover_paths:
                    # Guardar las 4 versiones en la base de datos
                    base_url = "/api/library/covers/"
                    book.cover_original = base_url + os.path.basename(cover_paths["original"])
                    book.cover_high = base_url + os.path.basename(cover_paths["high"])
                    book.cover_medium = base_url + os.path.basename(cover_paths["medium"])
                    book.cover_low = base_url + os.path.basename(cover_paths["low"])

            # session.commit()  # Movido a nivel de batch o fuente
            return outcome
        except Exception as e:
            logger.error(f"Error procesando libro {filepath}: {e}")
            session.rollback()
            return False

    def _generate_book_hash(self, book: LocalBook) -> str:
        """
        Genera un hash estable basado en: series + author + book_type + volume + translator + layout_by.
        """
        return hash_service.generate_book_hash(
            series=book.series,
            author=book.author,
            book_type=book.book_type,
            volume=book.volume,
            translator=book.translator,
            layout_by=book.layout_by,
            language=book.language,
            edition=book.edition,
            is_uncensored=book.is_uncensored or 0,
            color_mode=book.color_mode or "bw",
        )

    def _generate_series_hash(self, book: LocalBook) -> str:
        """
        Genera un hash estable para la serie basado en: series + author + book_type.
        """
        return hash_service.generate_series_hash(
            series=book.series or book.title,
            author=book.author,
            book_type=book.book_type,
        )

    def enrich_all_metadata(self, delay_seconds=2.0):
        """
        Busca metadatos online para libros que tienen ISBN pero les falta info,
        procesando uno a uno con esperas para evitar 429.
        """
        if ScannerService._is_scanning:
            logger.warning("No se puede enriquecer metadatos mientras hay un escaneo en curso.")
            return False

        from services.settings_service import get_setting

        if get_setting("enable_background_ai_scan", "false").lower() != "true":
            logger.info("🤖 AI Enrichment skipped (disabled by user setting).")
            return False

        ScannerService._is_scanning = True
        session = get_session()
        try:
            # Buscar libros con ISBN pero sin spanish_title o descripción
            books = (
                session.query(LocalBook)
                .filter(
                    LocalBook.isbn is not None,
                    LocalBook.isbn != "",
                    (LocalBook.spanish_title is None) | (LocalBook.description is None),
                )
                .all()
            )

            logger.info(f"Iniciando enriquecimiento manual para {len(books)} libros.")

            for i, book in enumerate(books):
                if self._enrich_from_isbn(book):
                    session.commit()
                    logger.info(f"[{i + 1}/{len(books)}] Enriquecido: {book.title}")
                    import time

                    time.sleep(delay_seconds)
                else:
                    # Si falla o no encuentra, no paramos pero notificamos
                    logger.debug(
                        f"[{i + 1}/{len(books)}] No se encontró info extra para: {book.title}"
                    )

            logger.info("Enriquecimiento masivo completado.")
            return True
        finally:
            session.close()
            ScannerService._is_scanning = False

    def _enrich_from_isbn(self, book):
        """
        Busca metadatos adicionales (títulos en inglés/español) usando Google Books API.
        Retorna True si encontró algo y lo aplicó.
        """
        import httpx

        try:
            if not book.isbn:
                return False
            isbn = re.sub(r"[^\d]", "", str(book.isbn))
            if not isbn:
                return False

            url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&hl=es"
            response = httpx.get(url, timeout=10.0)

            if response.status_code == 429:
                logger.warning("Google Books API rate limited (429). Esperando...")
                return False

            if response.status_code == 200:
                data = response.json()
                if data.get("totalItems", 0) > 0:
                    item = data["items"][0]["volumeInfo"]
                    api_title = item.get("title")
                    api_lang = item.get("language", "en")

                    found_something = False
                    if api_lang == "es":
                        if not book.spanish_title:
                            book.spanish_title = api_title
                            found_something = True
                    elif api_lang in ("ja", "jp"):
                        if not book.jap_title:
                            book.jap_title = api_title
                            found_something = True
                    else:
                        if not book.english_title:
                            book.english_title = api_title
                            found_something = True

                    if not book.description and item.get("description"):
                        book.description = item.get("description")
                        found_something = True

                    if found_something:
                        logger.info(f"Metadatos extraídos para ISBN {isbn}: {api_title}")
                        return True
        except Exception:
            pass

        return False

    def _copy_metadata_to_existing(self, source_book: LocalBook, target_book: LocalBook):
        """Helper to copy updated fields from a fresh scan to an existing DB record."""
        target_book.title = source_book.title
        target_book.romaji_title = source_book.romaji_title
        target_book.english_title = source_book.english_title
        target_book.spanish_title = source_book.spanish_title
        target_book.series = source_book.series
        target_book.volume = source_book.volume
        target_book.author = source_book.author
        target_book.author_jap = source_book.author_jap
        target_book.illustrator = source_book.illustrator
        target_book.illustrator_jap = source_book.illustrator_jap
        target_book.translator = source_book.translator
        target_book.layout_by = source_book.layout_by
        target_book.publisher = source_book.publisher
        target_book.description = source_book.description
        target_book.book_type = source_book.book_type
        target_book.tags = source_book.tags
        target_book.demographics = source_book.demographics
        target_book.series_hash = source_book.series_hash
        target_book.is_uncensored = source_book.is_uncensored
        target_book.color_mode = source_book.color_mode
        target_book.series_spanish = source_book.series_spanish
        target_book.series_english = source_book.series_english
        target_book.edition = source_book.edition
        target_book.isbn = source_book.isbn
        target_book.asin = source_book.asin
        target_book.epub_version = source_book.epub_version
        target_book.modified_at_opf = source_book.modified_at_opf
        target_book.word_count = source_book.word_count
        target_book.page_count = source_book.page_count
        target_book.reading_time = source_book.reading_time
        target_book.file_size = source_book.file_size

    @staticmethod
    def sync_series_metadata(session, series_hash: str):
        """
        Consolida la metadata de una serie basándose en todos sus volúmenes.
        1. Une los géneros (si un volumen tiene 'Sin Censura', la serie lo tiene).
        2. Recuenta volúmenes.
        3. Promedia ratings.
        """
        from models.library_models import LocalBook, SeriesMetadata

        series = session.query(SeriesMetadata).filter_by(series_hash=series_hash).first()
        if not series:
            return

        books = session.query(LocalBook).filter_by(series_hash=series_hash).all()
        if not books:
            # Archivar serie si ya no tiene libros
            from models.library_models import ArchivedSeries

            logger.info(
                f"Archivando serie vacía en sincronización de metadata: {series.series_name}"
            )
            archived_s = ArchivedSeries(
                series_name=series.series_name,
                series_spanish=series.series_spanish,
                series_english=series.series_english,
                series_hash=series.series_hash,
                author=series.author,
                description=series.description,
                tags=series.tags,
                cover_url=series.cover_url,
                book_type=series.book_type,
                publisher=series.publisher,
                original_series_id=series.id,
            )
            session.add(archived_s)
            session.delete(series)
            session.commit()
            return

        # 1. Consolidar Tags (Unión de todos los tags de todos los libros)
        all_tags = set()
        for b in books:
            if b.tags:
                all_tags.update(b.tags)

        # Mantener tags base que ya tuviera la serie (por si se agregaron manual)
        if series.tags:
            all_tags.update(series.tags)

        series.tags = list(all_tags)

        # 2. Otros campos (usar el primero que tenga info para los vacíos)
        if not series.description:
            for b in books:
                if b.description:
                    series.description = b.description
                    break

        # Prefer Spanish series name if available in any book
        if not series.series_spanish:
            for b in books:
                if hasattr(b, "series_spanish") and b.series_spanish:
                    series.series_spanish = b.series_spanish
                    break

        # Consolidate series_english
        if not series.series_english:
            for b in books:
                if hasattr(b, "series_english") and b.series_english:
                    series.series_english = b.series_english
                    break

        # 3. Synchronize Cover URL (Ensure it has one and it follows the new low-quality naming)
        if not series.cover_url or "_low.jpg" not in series.cover_url:
            for b in books:
                if b.cover_low:
                    series.cover_url = b.cover_low
                    break
                elif b.cover_medium:
                    series.cover_url = b.cover_medium
                    break

        # 3. Métricas
        series.book_count = len(books)

        ratings = [b.rating_average for b in books if b.rating_count > 0]
        if ratings:
            series.rating_average = sum(ratings) / len(ratings)

        series.rating_count = sum(b.rating_count for b in books)

        logger.info(f"🔄 Metadata de serie sincronizada: {series.series_name} ({len(books)} vols)")

    def _sync_translator_group(self, session, book):
        """
        Extrae traductor/siglas y asegura que existan en la tabla translators_groups.
        """
        from models.library_models import TranslatorsGroup

        translator = book.translator
        if not translator or translator == "Unknown":
            return

        # Intentar extraer siglas del filename si no están explícitas
        siglas = None
        if book.filename and "[" in book.filename and "]" in book.filename:
            matches = re.findall(r"\[(.*?)\]", book.filename)
            if matches:
                last_tag = matches[-1]
                # Si el tag es corto, probablemente sea la sigla (e.g. [GET])
                if 1 < len(last_tag) <= 10:
                    siglas = last_tag

        # Lógica de Upsert
        try:
            from sqlalchemy import func

            existing = (
                session.query(TranslatorsGroup)
                .filter(func.lower(TranslatorsGroup.name) == translator.lower())
                .first()
            )
            if existing:
                # Si no tiene siglas o las actuales son más largas que las detectadas, actualizar
                if siglas and (not existing.siglas or len(siglas) < len(existing.siglas or "")):
                    existing.siglas = siglas
            else:
                new_group = TranslatorsGroup(name=translator, siglas=siglas)
                session.add(new_group)
        except Exception as e:
            logger.warning(f"Error sincronizando grupo de traducción: {e}")

    @staticmethod
    def cleanup_library_orphans(session, user_id=None):
        """
        Verifica la existencia física de CADA libro en la base de datos local.
        IMPORTANTE: NO ELIMINA ARCHIVOS FÍSICOS. Solo actualiza la base de datos
        si el archivo YA NO ESTÁ en el disco.
        """
        logger.info("Iniciando Verificación de Integridad de la Librería...")

        from models.library_models import (
            ArchivedBook,
            ArchivedSeries,
            LibraryCleanupLog,
            LocalBook,
            SeriesMetadata,
        )

        deleted_books = 0
        deleted_series = 0
        affected_hashes = set()

        # 1. Obtener todos los libros
        books = session.query(LocalBook).all()
        total_checked = len(books)
        logger.info(f"Verificando existencia física de {total_checked} libros...")

        for book in books:
            # Protección de plataforma (Linux path on Windows)
            if book.filepath and book.filepath.startswith("/") and os.name == "nt":
                continue

            if not book.filepath or not os.path.exists(book.filepath):
                logger.warning(f"ARCHIVO NO ENCONTRADO EN DISCO: {book.filepath}")

                # Archivar registro de libro
                archived = ArchivedBook(
                    series_hash=book.series_hash,
                    book_hash=book.book_hash,
                    title=book.title,
                    filename=book.filename,
                    last_filepath=book.filepath,
                    volume=book.volume,
                    author=book.author,
                    book_type=book.book_type,
                    original_book_id=book.id,
                    reason="physically_missing_detected",
                )
                session.add(archived)

                if book.series_hash:
                    affected_hashes.add(book.series_hash)

                # Desvincular de tablas históricas para evitar ForeignKeyViolation
                from models.download_models import DownloadHistory
                from models.library_models import UserDownload, UserRating

                session.query(DownloadHistory).filter_by(book_id=book.id).update(
                    {DownloadHistory.book_id: None}
                )
                session.query(UserDownload).filter_by(book_id=book.id).update(
                    {UserDownload.book_id: None}
                )
                session.query(UserRating).filter_by(book_id=book.id).update(
                    {UserRating.book_id: None}
                )

                session.delete(book)
                deleted_books += 1

        session.commit()

        # 2. Verificar series huérfanas
        if affected_hashes:
            for s_hash in affected_hashes:
                count = session.query(LocalBook).filter_by(series_hash=s_hash).count()
                if count == 0:
                    series = session.query(SeriesMetadata).filter_by(series_hash=s_hash).first()
                    if series:
                        logger.info(f"Archivando serie ahora vacía: {series.series_name}")
                        archived_s = ArchivedSeries(
                            series_name=series.series_name,
                            series_spanish=series.series_spanish,
                            series_hash=series.series_hash,
                            author=series.author,
                            description=series.description,
                            tags=series.tags,
                            cover_url=series.cover_url,
                            book_type=series.book_type,
                            publisher=series.publisher,
                            original_series_id=series.id,
                        )
                        session.add(archived_s)
                        session.delete(series)
                        deleted_series += 1

            session.commit()

        # 3. Forzar Recálculo de Conteos para TODAS las series activas (mantenimiento preventivo)
        all_series = session.query(SeriesMetadata).all()
        for s in all_series:
            real_count = session.query(LocalBook).filter_by(series_hash=s.series_hash).count()
            if s.book_count != real_count:
                s.book_count = real_count

        session.commit()

        # 4. Registrar en el log histórico
        cleanup_log = LibraryCleanupLog(
            performed_by=user_id,
            total_books_checked=total_checked,
            missing_books_found=deleted_books,
            empty_series_removed=deleted_series,
            status="success",
        )
        session.add(cleanup_log)
        session.commit()

        return {
            "deleted_books": deleted_books,
            "deleted_series": deleted_series,
            "total_books": session.query(LocalBook).count(),
            "total_series": session.query(SeriesMetadata).count(),
        }
