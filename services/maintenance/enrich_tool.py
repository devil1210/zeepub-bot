import asyncio
import logging
from datetime import datetime
from typing import Any

from models.library_models import LocalBook
from services.maintenance.base import MaintenanceTool
from services.scanner.epub_scanner import EpubScanner
from utils.library_db import get_session

logger = logging.getLogger(__name__)


class MetadataEnrichmentTool(MaintenanceTool):
    @property
    def name(self) -> str:
        return "Enriquecimiento de Metadatos"

    @property
    def description(self) -> str:
        return "Busca metadatos online (ISBN) para completar información faltante."

    async def run(self, progress_callback=None, delay_seconds=2.0, **kwargs) -> dict[str, Any]:
        session = get_session()
        try:
            books = (
                session.query(LocalBook)
                .filter(
                    LocalBook.isbn.isnot(None),
                    LocalBook.isbn != "",
                    (LocalBook.spanish_title.is_(None)) | (LocalBook.description.is_(None)),
                )
                .all()
            )
            total = len(books)
            updated = 0

            logger.info(f"Starting metadata enrichment for {total} books")

            for i, book in enumerate(books):
                if await EpubScanner.enrich_from_isbn(book):
                    session.commit()
                    updated += 1

                if progress_callback:
                    await progress_callback(i + 1, total, f"Enriqueciendo {book.title}")

                await asyncio.sleep(delay_seconds)

            return {
                "success": True,
                "processed": total,
                "updated": updated,
                "finished_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in MetadataEnrichmentTool: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
