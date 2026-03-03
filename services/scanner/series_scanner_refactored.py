# services/scanner/series_scanner_refactored.py

import asyncio
import logging
from typing import Any

from models.library_models import LocalBook, MetadataProposal, SeriesMetadata

from .ai_processor import AIProcessor
from .metadata_processor import MetadataProcessor
from .slug_manager import SlugManager

logger = logging.getLogger(__name__)


class SeriesScannerRefactored:
    """
    Refactored series scanner using SOLID principles.
    Single Responsibility: Series coordination and orchestration.
    """

    def __init__(self):
        self.metadata_processor = MetadataProcessor()
        self.slug_manager = SlugManager()
        self.ai_processor = AIProcessor()

    @classmethod
    def get_or_create_series(cls, session: Any, book: LocalBook) -> SeriesMetadata:
        """
        Get or create series entry with improved separation of concerns.
        """
        try:
            # Extract and process metadata
            book_metadata = cls.metadata_processor.extract_and_normalize_metadata(book)

            # Check existing series
            series = session.query(SeriesMetadata).filter_by(series_hash=book.series_hash).first()

            if not series:
                series = cls._create_new_series(session, book, book_metadata)
            else:
                series = cls._update_existing_series(session, series, book, book_metadata)

            # Process AI proposals asynchronously
            asyncio.create_task(cls._process_ai_proposals(series.series_hash, book_metadata))

            return series

        except Exception as e:
            logger.error(f"❌ Error en get_or_create_series: {e}")
            raise

    @classmethod
    async def _process_ai_proposals(cls, session: Any, series_hash: str, book_metadata: dict) -> None:
        """Process AI proposals for series metadata improvement."""
        try:
            proposals = await cls.ai_processor.generate_metadata_proposals(series_hash, book_metadata)

            # Create proposals for review
            for proposal in proposals:
                p_obj = MetadataProposal(
                    series_hash=series_hash,
                    proposal_data=proposal,
                    status="pending",
                )
                session.add(p_obj)

            session.commit()
            logger.info(f"🌿 AI proposals generated: {len(proposals)} for {series_hash}")

        except Exception as e:
            logger.warning(f"Error processing AI proposals for {series_hash}: {e}")
        finally:
            pass

    @classmethod
    def _create_new_series(cls, session: Any, book: LocalBook, book_metadata: dict) -> SeriesMetadata:
        """
        Create new series with proper metadata processing.
        """
        logger.info(f"🆕 Creando nueva serie: {book_metadata.get('series', 'Sin título')}")

        # Create series with processed metadata
        series = SeriesMetadata(
            series_name=book_metadata.get("series", ""),
            series_spanish=book.series_spanish,
            series_english=book.series_english,
            series_hash=book.series_hash,
            author=book_metadata.get("author", ""),
            author_jap=book_metadata.get("author_jap"),
            illustrator=book_metadata.get("illustrator"),
            illustrator_jap=book_metadata.get("illustrator_jap"),
            description=book_metadata.get("description", ""),
            tags=book_metadata.get("tags", []),
            demographics=book_metadata.get("demographics", []),
            cover_url=book.cover_low or book.cover_medium,
            book_type=book_metadata.get("book_type", ""),
            publisher=book_metadata.get("publisher", ""),
            book_count=0,
            rating_average=0.0,
            rating_count=0,
        )

        # Generate and set slug
        slug = cls.slug_manager.generate_valid_slug(series)
        series.slug = slug

        session.add(series)
        session.flush()

        logger.info(f"✅ Nueva serie creada: {series.series_name} (slug: {slug})")
        return series

    @classmethod
    def _update_existing_series(
        cls, session: Any, series: SeriesMetadata, book: LocalBook, book_metadata: dict
    ) -> SeriesMetadata:
        """
        Update existing series with intelligent metadata merging.
        """
        logger.info(f"🔄 Actualizando serie existente: {series.series_name}")

        # Merge metadata using processor
        updated_series = cls.metadata_processor.merge_series_metadata(series, book_metadata)

        # Update slug safely
        cls.slug_manager.update_slug_safely(updated_series, book)

        session.commit()

        logger.info(f"✅ Serie actualizada: {updated_series.series_name}")
        return updated_series

    @classmethod
    def ai_gardener(cls, session: Any, limit: int = 50) -> None:
        """
        AI-powered metadata improvement and proposal generation.
        """
        logger.info(f"🤖 Iniciando AI Gardener (límite: {limit} series)")

        try:
            # Get series needing improvement
            series_query = (
                session.query(SeriesMetadata)
                .filter(
                    SeriesMetadata.description.is_(None)
                    | (SeriesMetadata.author.is_(None) & SeriesMetadata.rating_count < 5)
                )
                .limit(limit)
            )

            series_list = series_query.all()
            processed_count = 0

            for series in series_list:
                try:
                    # Generate AI proposals
                    current_metadata = series.to_dict()
                    proposals = cls.ai_processor.generate_metadata_proposals(series.series_hash, current_metadata)

                    # Create proposals for review
                    for proposal in proposals:
                        p_obj = MetadataProposal(
                            series_hash=series.series_hash,
                            proposal_data=proposal,
                            status="pending",
                        )
                        session.add(p_obj)

                    processed_count += 1

                except Exception as ae:
                    logger.warning(f"Error IA para {series.series_hash}: {ae}")

            session.commit()
            logger.info(f"🌿 AI Gardener completado: {processed_count} propuestas generadas")

        except Exception as e:
            logger.warning(f"Error AI Gardener: {e}")
