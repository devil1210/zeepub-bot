import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata
from services.maintenance.base import MaintenanceTool
from services.scanner.epub_scanner import EpubScanner
from services.scanner.series_scanner import SeriesScanner

logger = logging.getLogger(__name__)


class MetadataEnrichmentTool(MaintenanceTool):
    @property
    def name(self) -> str:
        return "Enriquecimiento de Metadatos"

    @property
    def description(self) -> str:
        return "Busca metadatos online (ISBN) para completar información faltante."

    async def run(self, progress_callback=None, delay_seconds=2.0, **kwargs) -> dict[str, Any]:
        try:
            async with pg_manager.get_session() as session:
                stmt = select(LocalBook).where(
                    LocalBook.isbn.isnot(None),
                    LocalBook.isbn != "",
                    (LocalBook.spanish_title.is_(None)) | (LocalBook.description.is_(None)),
                )
                result = await session.execute(stmt)
                books = result.scalars().all()
                total = len(books)
                updated = 0

                logger.info(f"Starting metadata enrichment for {total} books")

                for i, book in enumerate(books):
                    if await EpubScanner.enrich_from_isbn(book):
                        await session.commit()
                        updated += 1

                    if progress_callback:
                        await progress_callback(i + 1, total, f"Enriqueciendo Libro: {book.title}")

                    await asyncio.sleep(delay_seconds)

                # 2. Enriquecimiento de Series (IA)
                stmt_series = select(SeriesMetadata).where(
                    (SeriesMetadata.series_spanish.is_(None)) | (SeriesMetadata.series_spanish == "")
                )
                res_series = await session.execute(stmt_series)
                series_list = res_series.scalars().all()
                total_series = len(series_list)

                logger.info(f"Starting series enrichment for {total_series} series")

                for i, series in enumerate(series_list):
                    # Usamos explícitamente gemini-2.5-flash como pidió el usuario
                    await SeriesScanner.enrich_series_metadata(session, series, skip_ai=False)
                    await session.commit()

                    if progress_callback:
                        await progress_callback(i + 1, total_series, f"Enriqueciendo Serie: {series.series_name}")

                    await asyncio.sleep(delay_seconds)

                await session.commit()

            return {
                "success": True,
                "processed": total,
                "updated": updated,
                "finished_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in MetadataEnrichmentTool: {e}")
            return {"success": False, "error": str(e)}
