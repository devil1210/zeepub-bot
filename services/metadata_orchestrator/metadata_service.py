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
        from models.library import LocalBook

        try:
            async with pg_manager.get_session() as session:
                from sqlalchemy.orm import selectinload

                lb = None

                # Check if it's a known hash
                stmt_hash = (
                    select(LocalBook).options(selectinload(LocalBook.series_info)).where(LocalBook.book_hash == book_id)
                )
                res_hash = await session.execute(stmt_hash)
                lb = res_hash.scalar_one_or_none()

                # Fallback: try by ID
                if not lb:
                    id_str = str(book_id)
                    if id_str.startswith("series_"):
                        # Resolve the most relevant book of the series (usually volume 1)
                        s_hash = id_str.replace("series_", "")
                        stmt_s = (
                            select(LocalBook)
                            .options(selectinload(LocalBook.series_info))
                            .where(LocalBook.series_hash == s_hash)
                            .order_by(LocalBook.volume.asc())
                            .limit(1)
                        )
                        res_s = await session.execute(stmt_s)
                        lb = res_s.scalar_one_or_none()
                    elif id_str.startswith("local_") or id_str.isdigit():
                        clean_id = int(id_str.replace("local_", ""))
                        stmt_id = (
                            select(LocalBook)
                            .options(selectinload(LocalBook.series_info))
                            .where(LocalBook.id == clean_id)
                        )
                        res_id = await session.execute(stmt_id)
                        lb = res_id.scalar_one_or_none()

                # Fallback: try by path
                if not lb and ("/" in str(book_id) or "\\" in str(book_id)):
                    stmt_path = (
                        select(LocalBook)
                        .options(selectinload(LocalBook.series_info))
                        .where(LocalBook.filepath == book_id)
                    )
                    res_path = await session.execute(stmt_path)
                    lb = res_path.scalar_one_or_none()

                if lb:
                    res = lb.to_dict()
                    series = lb.series_info
                    if series:
                        res.update({
                            "series_name": series.name or "",
                            "serie": series.name or "",
                            "series": series.name or "",
                            "series_spanish": series.series_spanish or series.name or "",
                            "series_english": series.series_english or series.name or "",
                            "author": series.author or lb.author or "",
                            "autor": series.author or lb.author or "",
                            "author_jap": series.author_jap or lb.author_jap or "",
                            "illustrator": series.illustrator or lb.illustrator or "",
                            "illustrator_jap": series.illustrator_jap or lb.illustrator_jap or "",
                            "description": series.description or lb.description or "",
                            "sinopsis": series.description or lb.description or "",
                            "publisher": series.publisher or lb.publisher or "",
                            "editorial": lb.publisher or series.publisher or "",
                            "book_type": series.book_type or "Light Novel",
                            "tipo": series.book_type or "Light Novel",
                            "tags": series.tags_json or lb.tags_json or [],
                            "generos": series.tags_json or lb.tags_json or [],
                            "etiquetas": ", ".join(series.tags_json) if series.tags_json else "",
                            "demographics": series.demographics_json or lb.demographics_json or [],
                            "demography": series.demographics_json or lb.demographics_json or [],
                        })
                    else:
                        res.update({
                            "series_name": lb.series_spanish or lb.title,
                            "serie": lb.series_spanish or lb.title,
                            "series": lb.series_spanish or lb.title,
                            "series_spanish": lb.series_spanish or lb.title,
                            "series_english": lb.series_english or lb.title,
                            "autor": lb.author or "",
                            "sinopsis": lb.description or "",
                            "tipo": "Light Novel",
                            "generos": lb.tags_json or [],
                            "demographics": lb.demographics_json or [],
                            "demography": lb.demographics_json or [],
                        })
                    return res
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
