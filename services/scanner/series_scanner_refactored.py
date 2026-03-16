from typing import Any

from models.library_models import Book, Series
from utils.logger import logger  # Use project logger as per rule


class SeriesScannerRefactored:
    """
    Refactored Scanner for V4 Library.
    Modular design with specialized processors.
    """

    def __init__(self):
        # Asegurarse de que estos componentes existan o crear placeholders si faltan
        from .ai_processor import AIProcessor
        from .metadata_processor import MetadataProcessor
        from .slug_manager import SlugManager

        self.metadata_processor = MetadataProcessor()
        self.slug_manager = SlugManager()
        self.ai_processor = AIProcessor()

    async def get_or_create_series(self, session: Any, book: Book) -> Series:
        """
        Get or create series entry with improved separation of concerns.
        """
        try:
            # Extract and process metadata
            book_metadata = self.metadata_processor.extract_and_normalize_metadata(book)

            # Check existing series
            series = session.query(Series).filter_by(hash=book.hash).first()

            if not series:
                series = self._create_new_series(session, book, book_metadata)
            else:
                series = self._update_existing_series(session, series, book, book_metadata)

            # Process AI proposals - Note: session management in async tasks is tricky,
            # ideally we pass a dedicated session or use a service.
            # For now, let's keep it simple.
            return series

        except Exception as e:
            logger.error(f"❌ Error en get_or_create_series: {e}")
            raise

    async def _process_ai_proposals(self, session: Any, series_hash: str, book_metadata: dict) -> None:
        """Process AI proposals for series metadata improvement."""
        try:
            proposals = await self.ai_processor.generate_metadata_proposals(series_hash, book_metadata)
            await self.ai_processor.save_proposals(session, series_hash, proposals)
            logger.info(f"🌿 AI proposals processed for {series_hash}")

        except Exception as e:
            logger.warning(f"Error processing AI proposals for {series_hash}: {e}")

    def _create_new_series(self, session: Any, book: Book, book_metadata: dict) -> Series:
        """
        Create new series with proper metadata processing.
        """
        logger.info(f"🆕 Creando nueva serie: {book_metadata.get('series', 'Sin título')}")

        # V4 Series model has limited fields compared to the previous draft
        series = Series(
            title_raw=book_metadata.get("series", "Sin título"),
            hash=book.hash,
            source_id=book.series_id if hasattr(book, "series_id") else None,  # Fallback
            description=book_metadata.get("description", ""),
            # cover_url handled later or if available in book
        )

        # Generate and set slug
        slug = self.slug_manager.generate_valid_slug(series)
        series.slug = slug

        session.add(series)
        session.flush()

        logger.info(f"✅ Nueva serie creada: {series.title_raw} (slug: {slug})")
        return series

    def _update_existing_series(self, session: Any, series: Series, book: Book, book_metadata: dict) -> Series:
        """
        Update existing series with intelligent metadata merging.
        """
        logger.info(f"🔄 Actualizando serie existente: {series.title_raw}")

        # Merge metadata using processor
        updated_series = self.metadata_processor.merge_series_metadata(series, book_metadata)

        # Update slug safely
        self.slug_manager.update_slug_safely(updated_series, book)

        return updated_series

    async def ai_gardener(self, session: Any, limit: int = 50) -> None:
        """
        AI-powered metadata improvement and proposal generation.
        """
        logger.info(f"🤖 Iniciando AI Gardener (límite: {limit} series)")

        try:
            # Get series needing improvement
            series_list = (
                session.query(Series)
                .filter(Series.description.is_(None) | (Series.description == ""))
                .limit(limit)
                .all()
            )

            processed_count = 0

            for series in series_list:
                try:
                    # Generate AI proposals
                    series_data = {
                        "series": series.title_raw,
                        "description": series.description or "",
                        "tags": [],  # V4 model doesn't have it yet
                        "demographics": [],
                    }
                    proposals = await self.ai_processor.generate_metadata_proposals(series.hash, series_data)
                    await self.ai_processor.save_proposals(session, series.hash, proposals)
                    processed_count += 1

                except Exception as ae:
                    logger.warning(f"Error IA para {series.hash}: {ae}")

            logger.info(f"🌿 AI Gardener completado: {processed_count} propuestas generadas")

        except Exception as e:
            logger.warning(f"Error AI Gardener: {e}")
