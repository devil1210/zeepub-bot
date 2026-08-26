# services/scanner/slug_manager.py

import logging
import re

from models.library import LocalBook, SeriesMetadata
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

        # Remover sufijos de volumen del slug de la serie (ej: _V20 -> "")
        cleaned_slug = re.sub(r"_(?:v|vol|volumen|tomo)_\d+$", "", cleaned_slug, flags=re.IGNORECASE)
        cleaned_slug = re.sub(r"_(?:v|vol|volumen|tomo)\d+$", "", cleaned_slug, flags=re.IGNORECASE)

        return cleaned_slug

    @staticmethod
    def generate_valid_slug(series_metadata: SeriesMetadata) -> str:
        """
        Generate a valid slug from series metadata.
        """
        try:
            # Generate slug using existing utility
            meta_dict = series_metadata.to_dict()
            # Ensure name/series_name is present from the object directly if missing in dict
            candidate_name = series_metadata.series_name or series_metadata.name
            if candidate_name and candidate_name.strip().lower() in ("volumen único", "volumen unico", "volumen_unico"):
                candidate_name = series_metadata.series_spanish or series_metadata.series_english or ""

            if "series_name" not in meta_dict or not meta_dict["series_name"] or meta_dict["series_name"].strip().lower() in ("volumen único", "volumen unico"):
                meta_dict["series_name"] = candidate_name

            new_slug = generar_slug_from_meta(meta_dict)

            # Fallback total: si sigue vacío, usar el nombre directo o el hash
            if not new_slug and candidate_name:
                # Generación manual rápida si el helper falló
                new_slug = candidate_name.lower().replace(" ", "_")

            # Clean special characters and volume suffixes
            cleaned_slug = SlugManager.clean_slug_special_chars(new_slug)

            if not cleaned_slug:
                logger.warning(f"⚠️ Slug generado vacío para: {series_metadata.series_name}")

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

        # Detectar si el slug actual es genérico o inválido
        if current_slug.lower() in ("volumen_unico", "volumen_01", "volumen_1", "tomo_1", "tomo_01"):
            return True, "slug de volumen inválido"

        # Detectar si el slug actual contiene un sufijo de volumen (ej: _V20, _Vol_1)
        if re.search(r"_(?:v|vol|volumen|tomo)\d+$", current_slug, re.IGNORECASE) or re.search(r"_(?:v|vol|volumen|tomo)_\d+$", current_slug, re.IGNORECASE):
            return True, "contiene sufijo de volumen"

        if current_slug == new_slug:
            return False, "idéntico"

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
    def update_slug_safely(series: SeriesMetadata, book: LocalBook) -> str | None:
        """
        Update slug safely with validation and logging.
        """
        try:
            current_slug = series.slug or ""
            new_slug = SlugManager.generate_valid_slug(series)

            should_update, reason = SlugManager.should_update_slug(current_slug, new_slug, book.series_hash)

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
