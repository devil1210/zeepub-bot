import asyncio
import logging
from datetime import datetime
from typing import Any

from models.library_models import LocalBook
from services.maintenance.base import MaintenanceTool
from services.scanner.epub_scanner import EpubScanner
from utils.library_db import get_session

logger = logging.getLogger(__name__)


class CoverRefreshTool(MaintenanceTool):
    @property
    def name(self) -> str:
        return "Refresco de Portadas"

    @property
    def description(self) -> str:
        return "Extrae y actualiza las imágenes de portada de todos los libros EPUB."

    async def run(self, progress_callback=None, **kwargs) -> dict[str, Any]:
        session = get_session()
        try:
            books = session.query(LocalBook).all()
            total = len(books)
            updated = 0
            failed = 0

            logger.info(f"Starting cover refresh for {total} books")

            for i, book in enumerate(books):
                if await EpubScanner.refresh_book_cover(book.filepath, book, session):
                    updated += 1
                else:
                    failed += 1

                if progress_callback:
                    await progress_callback(i + 1, total, f"Procesando {book.title}")

                if (updated + failed) % 20 == 0:
                    session.commit()

                await asyncio.sleep(0.01)

            session.commit()

            return {
                "success": True,
                "processed": total,
                "updated": updated,
                "failed": failed,
                "finished_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in CoverRefreshTool: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
