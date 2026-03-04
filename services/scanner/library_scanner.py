import logging
import os
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload

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
    async def sync_translator_group(session: Any, book: LocalBook):
        """
        Extrae traductor y asegura que exista en la tabla translators_groups.
        """
        import re

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
            stmt = select(TranslatorsGroup).where(func.lower(TranslatorsGroup.name) == translator.lower())
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                if siglas and (not existing.siglas or len(siglas) < len(existing.siglas or "")):
                    existing.siglas = siglas
            else:
                new_group = TranslatorsGroup(name=translator, siglas=siglas)
                session.add(new_group)

            # Flush to get ID if needed, but usually we commit in batches elsewhere
            await session.flush()
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
            stmt = (
                select(LocalBook).options(selectinload(LocalBook.series_info)).where(LocalBook.source_id == source.id)
            )
            result = await session.execute(stmt)
            db_books = result.scalars().all()

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
                        author=b.series_info.author if b.series_info else "Unknown",
                        book_type=b.series_info.book_type if b.series_info else "Light Novel",
                        original_book_id=b.id,
                        reason="physically_deleted",
                    )
                    session.add(archived)
                    archived_count += 1

                    # Desvincular - PostgreSQL async style
                    await session.execute(
                        update(DownloadHistory).where(DownloadHistory.book_id == b.id).values(book_id=None)
                    )
                    await session.execute(update(UserDownload).where(UserDownload.book_id == b.id).values(book_id=None))
                    await session.execute(update(UserRating).where(UserRating.book_id == b.id).values(book_id=None))

                    await session.delete(b)
                    removed_count += 1

            await session.flush()
            return archived_count, removed_count
        except Exception as e:
            logger.error(f"Error en pruning de {source.name}: {e}")
            await session.rollback()
            return 0, 0

    @staticmethod
    async def resolve_orphans(session: Any, scanned_source_ids: list) -> tuple[int, int]:
        """
        Detecta libros que pertenecen a fuentes no escaneadas o inexistentes.
        """
        if not scanned_source_ids:
            return 0, 0

        stmt = select(LocalBook).where(LocalBook.source_id.notin_(scanned_source_ids))
        result = await session.execute(stmt)
        orphans = result.scalars().all()

        if not orphans:
            return 0, 0

        logger.warning(f"⚠️ {len(orphans)} libros huérfanos detectados.")

        count_moved = 0
        for orphan in orphans:
            dup_stmt = select(DuplicateBook).where(DuplicateBook.duplicate_filepath == orphan.filepath)
            dup_result = await session.execute(dup_stmt)
            exists = dup_result.scalar_one_or_none()

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
            await session.delete(orphan)

        await session.flush()
        return len(orphans), count_moved

    @staticmethod
    async def cleanup_library_orphans(session: Any, user_id: int = None) -> dict:
        """
        Verificación manual/profunda de integridad física de toda la librería.
        """
        logger.info("Iniciando auditoría de integridad física...")

        from models.download_models import DownloadHistory
        from models.library_models import UserDownload, UserRating

        stmt = select(LocalBook)
        result = await session.execute(stmt)
        books = result.scalars().all()

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

                await session.execute(
                    update(DownloadHistory).where(DownloadHistory.book_id == book.id).values(book_id=None)
                )
                await session.execute(update(UserDownload).where(UserDownload.book_id == book.id).values(book_id=None))
                await session.execute(update(UserRating).where(UserRating.book_id == book.id).values(book_id=None))

                await session.delete(book)
                deleted_books += 1

        await session.flush()

        # Limpieza de series vacías
        # Subquery for exists
        lb_exists = select(LocalBook).where(LocalBook.series_hash == SeriesMetadata.series_hash).exists()
        empty_series_stmt = select(SeriesMetadata).where(~lb_exists)
        empty_series_result = await session.execute(empty_series_stmt)
        empty_series = empty_series_result.scalars().all()

        for s in empty_series:
            # Verificar si ya existe en archived_series para evitar duplicate key
            arch_stmt = select(ArchivedSeries).where(ArchivedSeries.series_hash == s.series_hash)
            arch_result = await session.execute(arch_stmt)
            existing = arch_result.scalar_one_or_none()

            if not existing:
                archived_s = ArchivedSeries(
                    series_name=s.series_name,
                    series_spanish=s.series_spanish,
                    series_english=s.series_english,
                    series_hash=s.series_hash,
                    author=s.author,
                    author_jap=s.author_jap,
                    description=s.description,
                    tags=s.tags,
                    demographics=s.demographics,
                    book_type=s.book_type,
                    publisher=s.publisher,
                    slug=s.slug,
                    original_series_id=s.id,
                )
                session.add(archived_s)
            await session.delete(s)
            deleted_series += 1

        await session.flush()

        log = LibraryCleanupLog(
            performed_by=user_id,
            total_books_checked=total_checked,
            missing_books_found=deleted_books,
            empty_series_removed=deleted_series,
            status="success",
        )
        session.add(log)
        await session.flush()

        # Count total books
        count_stmt = select(func.count()).select_from(LocalBook)
        count_result = await session.execute(count_stmt)
        total_books_count = count_result.scalar()

        return {
            "deleted_books": deleted_books,
            "deleted_series": deleted_series,
            "total_books": total_books_count,
        }
