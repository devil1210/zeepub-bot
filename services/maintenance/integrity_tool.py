import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, update

from core.db_manager_pg import pg_manager
from models.library_models import Book, Series
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
                # 1. Buscar hashes de series que tienen libros sin vincular
                stmt_unlinked = (
                    select(Book.series_hash).where(Book.series_id.is_(None), Book.series_hash.is_not(None)).distinct()
                )

                # 2. También incluir todas las series para "sanar" nombres y tags si es necesario
                stmt_all_series = select(Series.series_hash)

                from sqlalchemy import union

                stmt = union(stmt_unlinked, stmt_all_series)

                result = await session.execute(stmt)
                hashes = result.scalars().all()
                total = len(hashes)

                if total == 0:
                    logger.info("Integrity check: No unlinked books found.")
                    return {
                        "success": True,
                        "stats": stats,
                        "message": "Library is healthy",
                        "finished_at": datetime.utcnow().isoformat(),
                    }

                logger.info(f"Integrity check: Processing {total} unlinked series hashes...")

                for i, s_hash in enumerate(hashes):
                    # 2. Re-verificar la serie y sus nombres
                    series_stmt = select(Series).where(Series.series_hash == s_hash)
                    series_res = await session.execute(series_stmt)
                    series = series_res.scalar_one_or_none()

                    if series:
                        # Vincular todos los libros con este hash
                        update_stmt = (
                            update(Book)
                            .where(Book.series_hash == s_hash)
                            .where(Book.series_id.is_(None))
                            .values(series_id=series.id)
                        )
                        upd_res = await session.execute(update_stmt)
                        stats["books_linked"] += upd_res.rowcount
                        stats["series_hashes_processed"] += 1
                    else:
                        stats["skipped"] += 1
                        logger.debug(f"Integrity: No Series found for hash {s_hash}")

                    if progress_callback:
                        await progress_callback(i + 1, total, f"Vinculando serie {s_hash[:8]}...")

                    # Commit parcial para evitar transacciones gigantes
                    if (i + 1) % 100 == 0:
                        await session.commit()

                await session.commit()

                await session.commit()

            logger.info(f"✅ Integrity tool finished. Linked {stats['books_linked']} books.")
            return {
                "success": True,
                "stats": stats,
                "finished_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in DatabaseIntegrityTool: {e}")
            return {"success": False, "error": str(e)}
