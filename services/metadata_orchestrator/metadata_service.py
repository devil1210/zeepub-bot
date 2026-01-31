import logging
from typing import Any

logger = logging.getLogger(__name__)


class MetadataOrchestrator:
    """
    Coordinates metadata extraction and enrichment from multiple sources.
    """

    async def resolve_book(self, book_id: str) -> dict[str, Any] | None:
        """
        Tries to find a book by its various identifiers (hash, local_id, path).
        """
        if not book_id:
            return None

        # 1. Search in Local PostgreSQL
        from sqlalchemy import select

        from core.db_manager_pg import pg_manager
        from models.library_models import LocalBook

        try:
            async with pg_manager.get_session() as session:
                lb = None

                # Check if it's a known hash
                stmt_hash = select(LocalBook).where(LocalBook.book_hash == book_id)
                res_hash = await session.execute(stmt_hash)
                lb = res_hash.scalar_one_or_none()

                # Fallback: try by ID
                if not lb and (
                    str(book_id).startswith("local_") or str(book_id).isdigit()
                ):
                    clean_id = int(str(book_id).replace("local_", ""))
                    stmt_id = select(LocalBook).where(LocalBook.id == clean_id)
                    res_id = await session.execute(stmt_id)
                    lb = res_id.scalar_one_or_none()

                # Fallback: try by path
                if not lb and ("/" in str(book_id) or "\\" in str(book_id)):
                    stmt_path = select(LocalBook).where(LocalBook.filepath == book_id)
                    res_path = await session.execute(stmt_path)
                    lb = res_path.scalar_one_or_none()

                if lb:
                    return lb.to_dict()
        except Exception as e:
            logger.error(f"MetadataOrchestrator error resolving book {book_id}: {e}")

        # 2. Check OPDS/Cache (Future)

        return None

    async def get_enriched_metadata(
        self, book_id: str, source: str = "auto", epub_bytes: bytes | None = None
    ) -> dict[str, Any]:
        """
        Gathers metadata from the primary source and enriches it with others if available.
        """
        metadata = {}

        # 1. Resolve base book data
        book_data = await self.resolve_book(book_id)
        if book_data:
            metadata = book_data

        # 2. Enrichment from EPUB file if provided
        if epub_bytes:
            from services.epub_service import enrich_metadata_from_epub

            metadata = await enrich_metadata_from_epub(epub_bytes, book_id, metadata)

        # 3. Normalization logic
        from utils.helpers import parse_metadata_from_title

        title = metadata.get("title", "")
        if title:
            parsed = parse_metadata_from_title(title)
            # Merge missing fields
            for k, v in parsed.items():
                if not metadata.get(k):
                    metadata[k] = v

        return metadata


metadata_orchestrator = MetadataOrchestrator()
