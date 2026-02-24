import logging
import os
from typing import Any

from models.library_models import (
    ArchivedBook,
    ArchivedSeries,
    DuplicateBook,
    LibraryCleanupLog,
    LibrarySource,
    LocalBook,
    SeriesMetadata,
    TranslatorsGroup,
)

logger = logging.getLogger(__name__)


class LibraryScanner:
    """
    Módulo encargado del mantenimiento global de la librería:
    limpieza de archivos eliminados, detección de huérfanos e integridad.
    """

    @staticmethod
    def sync_translator_group(session: Any, book: LocalBook):
        """
        Extrae traductor y asegura que exista en la tabla translators_groups.
        """
        import re

        from sqlalchemy import func

        translator = book.translator
        if not translator or translator == "Unknown":
            return

        siglas = None
        if book.filename and "[" in book.filename and "]" in book.filename:
            matches = re.findall(r"\[(.*?)\]", book.filename)
            if matches:
                last_tag = matches[-1]
                if 1 < len(last_tag) <= 10:
                    siglas = last_tag

        try:
            existing = (
                session.query(TranslatorsGroup).filter(func.lower(TranslatorsGroup.name) == translator.lower()).first()
            )
            if existing:
                if siglas and (not existing.siglas or len(siglas) < len(existing.siglas or "")):
                    existing.siglas = siglas
            else:
                new_group = TranslatorsGroup(name=translator, siglas=siglas)
                session.add(new_group)
        except Exception as e:
            logger.warning(f"Error sincronizando grupo traductor: {e}")

    @staticmethod
    async def prune_source(session: Any, source: LibrarySource, found_files: set[str]) -> tuple[int, int]:
        """
        Archiva libros que están en la DB pero ya no existen físicamente en la fuente.
        """
        archived_count = 0
        removed_count = 0

        try:
            db_books = session.query(LocalBook).filter(LocalBook.source_id == source.id).all()
            db_paths = {b.filepath for b in db_books}

            missing_paths = db_paths - found_files
            if not missing_paths:
                return 0, 0

            logger.info(f"Detectados {len(missing_paths)} libros eliminados en {source.name}. Archivando...")

            from models.download_models import DownloadHistory
            from models.library_models import UserDownload, UserRating

            for b in db_books:
                if b.filepath in missing_paths:
                    # Archivar
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
                    archived_count += 1

                    # Desvincular
                    session.query(DownloadHistory).filter_by(book_id=b.id).update({DownloadHistory.book_id: None})
                    session.query(UserDownload).filter_by(book_id=b.id).update({UserDownload.book_id: None})
                    session.query(UserRating).filter_by(book_id=b.id).update({UserRating.book_id: None})

                    session.delete(b)
                    removed_count += 1

            session.commit()
            return archived_count, removed_count
        except Exception as e:
            logger.error(f"Error en pruning de {source.name}: {e}")
            session.rollback()
            return 0, 0

    @staticmethod
    def resolve_orphans(session: Any, scanned_source_ids: list) -> tuple[int, int]:
        """
        Detecta libros que pertenecen a fuentes no escaneadas o inexistentes.
        """
        if not scanned_source_ids:
            return 0, 0

        orphans = session.query(LocalBook).filter(LocalBook.source_id.notin_(scanned_source_ids)).all()
        if not orphans:
            return 0, 0

        logger.warning(f"⚠️ {len(orphans)} libros huérfanos detectados.")

        count_moved = 0
        for orphan in orphans:
            exists = session.query(DuplicateBook).filter_by(duplicate_filepath=orphan.filepath).first()
            if not exists:
                dup = DuplicateBook(
                    book_hash=orphan.book_hash,
                    original_filepath="ORPHAN_RECORD",
                    duplicate_filepath=orphan.filepath,
                    title=f"[HUÉRFANO] {orphan.title}",
                    author=orphan.author,
                )
                session.add(dup)
                count_moved += 1
            session.delete(orphan)

        session.commit()
        return len(orphans), count_moved

    @staticmethod
    async def cleanup_library_orphans(session: Any, user_id: int = None) -> dict:
        """
        Verificación manual/profunda de integridad física de toda la librería.
        """
        logger.info("Iniciando auditoría de integridad física...")

        from models.download_models import DownloadHistory
        from models.library_models import UserDownload, UserRating

        books = session.query(LocalBook).all()
        deleted_books = 0
        deleted_series = 0
        total_checked = len(books)

        for book in books:
            if book.filepath and book.filepath.startswith("/") and os.name == "nt":
                continue

            if not book.filepath or not os.path.exists(book.filepath):
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

                session.query(DownloadHistory).filter_by(book_id=book.id).update({DownloadHistory.book_id: None})
                session.query(UserDownload).filter_by(book_id=book.id).update({UserDownload.book_id: None})
                session.query(UserRating).filter_by(book_id=book.id).update({UserRating.book_id: None})

                session.delete(book)
                deleted_books += 1

        session.commit()

        # Limpieza de series vacías
        empty_series = (
            session.query(SeriesMetadata)
            .filter(~session.query(LocalBook).filter(LocalBook.series_hash == SeriesMetadata.series_hash).exists())
            .all()
        )

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
            deleted_series += 1

        session.commit()

        log = LibraryCleanupLog(
            performed_by=user_id,
            total_books_checked=total_checked,
            missing_books_found=deleted_books,
            empty_series_removed=deleted_series,
            status="success",
        )
        session.add(log)
        session.commit()

        return {
            "deleted_books": deleted_books,
            "deleted_series": deleted_series,
            "total_books": session.query(LocalBook).count(),
        }
