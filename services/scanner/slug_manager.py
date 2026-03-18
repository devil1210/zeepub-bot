# services/scanner/slug_manager.py

import logging
import re

from models.library_models import Book, Series
from utils.helpers import generar_slug_from_meta

logger = logging.getLogger(__name__)


class SlugManager:
    """
    Handle slug generation, validation, and correction.
    Single Responsibility: Slug operations and URL/hashtag compatibility.
    """

    @staticmethod
    def clean_slug_special_chars(slug: str) -> str:
        """
        Clean slug of special characters not allowed in URLs/hashtags.
        """
        if not slug:
            return ""

        # Characters not permitted in slugs
        invalid_chars = [
            "!",
            "?",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "+",
            "=",
            "[",
            "]",
            "{",
            "}",
            "|",
            "\\",
            ":",
            ";",
            '"',
            "'",
            "<",
            ">",
            ",",
            "/",
            "`",
            "~",
        ]

        cleaned_slug = slug
        for char in invalid_chars:
            cleaned_slug = cleaned_slug.replace(char, "")

        # Clean multiple spaces and consecutive hyphens
        cleaned_slug = re.sub(r"\s+", "_", cleaned_slug)
        cleaned_slug = re.sub(r"_+", "_", cleaned_slug)
        cleaned_slug = cleaned_slug.strip("_")

        return cleaned_slug

    @staticmethod
    def generate_valid_slug(series: Series) -> str:
        """
        Generate a valid slug from series metadata.
        """
        try:
            # Generate slug using existing utility
            series_data = {
                "title_raw": series.title_raw,
                "title_spanish": series.title_spanish,
                "title_english": series.title_english,
            }
            new_slug = generar_slug_from_meta(series_data)

            # Clean special characters
            cleaned_slug = SlugManager.clean_slug_special_chars(new_slug)

            logger.info(f"🔗 Slug generado: {cleaned_slug}")
            return cleaned_slug

        except Exception as e:
            logger.error(f"❌ Error generando slug: {e}")
            return ""

    @staticmethod
    def should_update_slug(current_slug: str, new_slug: str, series_hash: str) -> tuple[bool, str]:
        """
        Determine if a slug should be updated.
        """
        if not current_slug:
            return True, "vacío"

        if current_slug == new_slug:
            return True, "idéntico"

        # Check if current slug has special characters
        has_special_chars = any(
            char in current_slug
            for char in [
                "!",
                "?",
                "#",
                "$",
                "%",
                "^",
                "&",
                "*",
                "(",
                ")",
                "+",
                "=",
                "[",
                "]",
                "{",
                "}",
                "|",
                "\\",
                ":",
                ";",
                '"',
                "'",
                "<",
                ">",
                ",",
                "/",
                "`",
                "~",
            ]
        )

        if has_special_chars:
            return True, "contiene caracteres especiales"

        # Check if current slug looks auto-generated
        is_auto_generated = (
            len(current_slug) > 40  # Hash residual muy largo
            or current_slug == str(series_hash)[:40]  # Igual al hash
        )

        if is_auto_generated:
            return True, "auto-generado"

        return False, "manual preservado"

    @staticmethod
    def update_slug_safely(series: Series, book: Book) -> str | None:
        """
        Update slug safely with validation and logging.
        """
        try:
            current_slug = series.slug or ""
            new_slug = SlugManager.generate_valid_slug(series)

            should_update, reason = SlugManager.should_update_slug(current_slug, new_slug, book.hash)

            if should_update:
                series.slug = new_slug
                logger.info(f"📝 Slug actualizado ({reason}): {current_slug} → {new_slug}")
                return new_slug
            else:
                logger.info(f"🔒 Slug preservado ({reason}): {current_slug}")
                return current_slug

        except Exception as e:
            logger.error(f"❌ Error actualizando slug: {e}")
            return None
