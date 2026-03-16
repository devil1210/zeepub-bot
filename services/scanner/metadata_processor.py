# services/scanner/metadata_processor.py

import logging
from typing import Any

from models.library_models import Book, Series
from utils.helpers import parse_metadata_from_title

logger = logging.getLogger(__name__)


class MetadataProcessor:
    """
    Handle metadata processing and normalization for series.
    Single Responsibility: Metadata extraction, validation, and normalization.
    """

    @staticmethod
    def extract_and_normalize_metadata(book: Book) -> dict[str, Any]:
        """
        Extract and normalize metadata from book data.
        """
        try:
            # Parse metadata with special character preservation
            parsed = parse_metadata_from_title(book.title, preserve_special_chars=True)

            # Normalize extracted data
            metadata = {
                "series": parsed.get("series", ""),
                "series_clean": parsed.get("series_clean", ""),
                "volume": parsed.get("volume", ""),
                "clean_title": parsed.get("clean_title", ""),
                "tags": parsed.get("tags", []),
                "romaji": parsed.get("romaji", ""),
                "author": "",  # V4 Series entity holds metadata, Book is file-centric
                "illustrator": "",
                "publisher": "",
                "book_type": "",
                "description": "",
                "demographics": [],
            }

            # Validate and clean metadata
            validated_metadata = MetadataProcessor._validate_metadata(metadata)

            logger.info(f"📊 Metadata procesada para: {book.title}")
            return validated_metadata

        except Exception as e:
            logger.error(f"❌ Error procesando metadata para {book.title}: {e}")
            return {}

    @staticmethod
    def _validate_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and clean metadata fields.
        """
        validated = {}

        for key, value in metadata.items():
            if isinstance(value, str):
                # Clean string values
                validated[key] = value.strip() if value.strip() else ""
            elif isinstance(value, list):
                # Clean list values
                validated[key] = [item.strip() for item in value if item and item.strip()]
            else:
                validated[key] = value

        return validated

    @staticmethod
    def merge_series_metadata(series: Series, book_metadata: dict[str, Any]) -> Series:
        """
        Merge book metadata into series metadata with conflict resolution.
        """
        try:
            # Update fields only if they're better or empty
            if book_metadata.get("author") and not series.author:
                series.author = book_metadata["author"]
                logger.info(f"📝 Actualizado autor: {series.author}")

            if book_metadata.get("illustrator") and not series.illustrator:
                series.illustrator = book_metadata["illustrator"]
                logger.info(f"📝 Actualizado ilustrador: {series.illustrator}")

            if book_metadata.get("publisher") and not series.publisher:
                series.publisher = book_metadata["publisher"]
                logger.info(f"📝 Actualizado editorial: {series.publisher}")

            if book_metadata.get("book_type") and not series.book_type:
                series.book_type = book_metadata["book_type"]
                logger.info(f"📝 Actualizado tipo: {series.book_type}")

            if book_metadata.get("description") and not series.description:
                series.description = book_metadata["description"]
                logger.info(f"📝 Actualizada descripción: {series.description}")

            # Handle demographics merge
            if book_metadata.get("demographics"):
                existing_demos = set(series.demographics or [])
                new_demos = set(book_metadata["demographics"])
                merged_demos = existing_demos.union(new_demos)
                series.demographics = list(merged_demos)
                logger.info(f"📝 Actualizados demographics: {len(merged_demos)} géneros")

            return series

        except Exception as e:
            logger.error(f"❌ Error fusionando metadata: {e}")
            return series
