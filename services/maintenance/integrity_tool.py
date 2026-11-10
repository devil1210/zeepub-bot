import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library import LocalBook, SeriesMetadata
from services.maintenance.base import MaintenanceTool

logger = logging.getLogger(__name__)


class DatabaseIntegrityTool(MaintenanceTool):
    """
    Herramienta de mantenimiento para asegurar que todos los libros estén vinculados
    correctamente a sus metadatos de serie y corregir inconsistencias silenciosas.
    """

    @property
    def name(self) -> str:
        return "Integridad de Base de Datos"

    @property
    def description(self) -> str:
        return "Vincula libros con sus metadatos de serie y asegura integridad referencial."

    async def run(self, progress_callback=None, **kwargs) -> dict[str, Any]:
        stats = {"books_linked": 0, "series_hashes_processed": 0, "skipped": 0}

        try:
            async with pg_manager.get_session() as session:
                # 1. Buscar hashes de series en libros
                stmt = (
                    select(LocalBook.series_id)
                    .where(LocalBook.series_id.is_not(None))
                    .distinct()
                )

                result = await session.execute(stmt)
                hashes = result.scalars().all()
                total = len(hashes)

                if total == 0:
                    logger.info("Integrity check: No series hashes found in books.")
                    return {
                        "success": True,
                        "stats": stats,
                        "message": "Library is healthy",
                        "finished_at": datetime.utcnow().isoformat(),
                    }

                logger.info(f"Integrity check: Processing {total} series hashes...")

                for i, s_hash in enumerate(hashes):
                    # 2. Re-verificar la serie (buscando por hash semántico)
                    series_stmt = select(SeriesMetadata).where(
                        SeriesMetadata.series_hash == s_hash
                    )
                    series_res = await session.execute(series_stmt)
                    series = series_res.scalar_one_or_none()

                    if series:
                        stats["series_hashes_processed"] += 1
                        # En v4 la vinculación es directa por hash
                    else:
                        stats["skipped"] += 1
                        logger.debug(
                            f"Integrity: No SeriesMetadata found for hash {s_hash}"
                        )

                    if progress_callback:
                        await progress_callback(
                            i + 1, total, f"Verificando serie {s_hash[:8]}..."
                        )

                    # Commit parcial para evitar transacciones gigantes
                    if (i + 1) % 100 == 0:
                        await session.commit()

                await session.commit()

                # 3. Limpieza de libros duplicados por filepath
                from sqlalchemy import func

                dup_stmt = (
                    select(LocalBook.filepath)
                    .group_by(LocalBook.filepath)
                    .having(func.count(LocalBook.id) > 1)
                )
                dup_res = await session.execute(dup_stmt)
                dup_fps = list(dup_res.scalars().all())
                stats["duplicates_purged"] = 0

                if dup_fps:
                    logger.info(
                        f"Integrity check: Encontradas {len(dup_fps)} rutas con registros duplicados. Limpiando..."
                    )
                    from services.scanner.library_scanner import LibraryScanner

                    for dfp in dup_fps:
                        b_stmt = (
                            select(LocalBook)
                            .where(LocalBook.filepath == dfp)
                            .order_by(LocalBook.created_at.desc())
                        )
                        b_res = await session.execute(b_stmt)
                        b_rows = list(b_res.scalars().all())
                        if len(b_rows) > 1:
                            for old_dup in b_rows[1:]:
                                await LibraryScanner._cleanup_book_references(
                                    session, old_dup.book_hash
                                )
                                await session.delete(old_dup)
                                stats["duplicates_purged"] += 1
                    await session.commit()

            logger.info(
                f"✅ Integrity tool finished. Processed {stats['series_hashes_processed']} series hashes."
            )
            return {
                "success": True,
                "stats": stats,
                "finished_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in DatabaseIntegrityTool: {e}")
            return {"success": False, "error": str(e)}
