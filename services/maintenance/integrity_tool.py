import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_, select, update

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata
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
                    select(LocalBook.series_hash)
                    .where(LocalBook.series_metadata_id.is_(None), LocalBook.series_hash.is_not(None))
                    .distinct()
                )

                # 2. También incluir todas las series para "sanar" nombres y tags si es necesario
                stmt_all_series = select(SeriesMetadata.series_hash)

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
                    series_stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash == s_hash)
                    series_res = await session.execute(series_stmt)
                    series = series_res.scalar_one_or_none()

                    if series:
                        # Auto-heal series_name: Preferir series_english (el limpio) sobre el raw si es posible
                        old_name = series.series_name
                        if series.series_english and series.series_english != series.series_name:
                            # Heurística: Si el nombre actual tiene mucho Romaji o es sospechoso,
                            # o simplemente si series_english existe y no es el slug hash
                            series.series_name = series.series_english
                            logger.info(f"Integrity: Healed name for {s_hash[:8]}: {old_name} -> {series.series_name}")

                        # Vincular todos los libros con este hash
                        update_stmt = (
                            update(LocalBook)
                            .where(LocalBook.series_hash == s_hash)
                            .where(LocalBook.series_metadata_id.is_(None))
                            .values(series_metadata_id=series.id)
                        )
                        upd_res = await session.execute(update_stmt)
                        stats["books_linked"] += upd_res.rowcount
                        stats["series_hashes_processed"] += 1
                    else:
                        stats["skipped"] += 1
                        logger.debug(f"Integrity: No SeriesMetadata found for hash {s_hash}")

                    if progress_callback:
                        await progress_callback(i + 1, total, f"Vinculando serie {s_hash[:8]}...")

                    # Commit parcial para evitar transacciones gigantes
                    if (i + 1) % 100 == 0:
                        await session.commit()

                await session.commit()

                # 3. Merge Duplicate Series: Fusionar metadatos que tienen el mismo nombre canónico
                logger.info("Integrity check: Starting series merge phase...")
                # Agrupamos por nombre (insensible a mayúsculas) y contamos
                subq_dup = (
                    select(func.lower(SeriesMetadata.series_name).label("name"))
                    .group_by(func.lower(SeriesMetadata.series_name))
                    .having(func.count(SeriesMetadata.id) > 1)
                    .subquery()
                )

                stmt_dup_groups = (
                    select(SeriesMetadata)
                    .join(subq_dup, func.lower(SeriesMetadata.series_name) == subq_dup.c.name)
                    .order_by(func.lower(SeriesMetadata.series_name))
                )
                res_dups = await session.execute(stmt_dup_groups)
                dup_entities = res_dups.scalars().all()

                # Agrupar en memoria las entidades de base de datos
                merge_groups = {}
                for s in dup_entities:
                    key = s.series_name.lower()
                    if key not in merge_groups:
                        merge_groups[key] = []
                    merge_groups[key].append(s)

                for _, entities in merge_groups.items():
                    # Pick Master: The one with most books or a cover
                    entities.sort(key=lambda x: (x.book_count, 1 if x.cover_url else 0), reverse=True)
                    master = entities[0]
                    duplicates = entities[1:]

                    logger.info(
                        f"Merging {len(duplicates)} duplicates into master series: {master.series_name} ({master.series_hash[:8]})"
                    )

                    for dup in duplicates:
                        # 1. Update books to point to master
                        upd_books = (
                            update(LocalBook)
                            .where(
                                or_(LocalBook.series_metadata_id == dup.id, LocalBook.series_hash == dup.series_hash)
                            )
                            .values(series_metadata_id=master.id, series_hash=master.series_hash)
                        )
                        await session.execute(upd_books)

                        # 2. Delete duplicate metadata
                        from sqlalchemy import delete

                        await session.execute(delete(SeriesMetadata).where(SeriesMetadata.id == dup.id))

                    # Recalcular book_count del master
                    count_q = select(func.count(LocalBook.id)).where(LocalBook.series_metadata_id == master.id)
                    count_res = await session.execute(count_q)
                    master.book_count = count_res.scalar() or 0

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
