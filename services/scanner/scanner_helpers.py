# services/scanner/scanner_helpers.py

import logging
import re
from typing import Any

from sqlalchemy import select

logger = logging.getLogger(__name__)


class ScannerHelpers:
    """
    Utility functions for scanner operations.
    Single Responsibility: Common helper functions and utilities.
    """

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text content.
        """
        if not text:
            return ""

        # Remove extra whitespace and normalize
        cleaned = text.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"[^\w\s\-\.,]", "", cleaned)

        return cleaned.strip()

    @staticmethod
    def validate_title(title: str) -> dict[str, Any]:
        """
        Validate and extract title information.
        """
        if not title:
            return {"valid": False, "reason": "Título vacío"}

        # Check minimum length
        if len(title) < 2:
            return {"valid": False, "reason": "Título demasiado corto"}

        # Check for valid characters
        if not re.match(r"^[\w\s\-\.,]+$", title):
            return {"valid": False, "reason": "Título contiene caracteres inválidos"}

        return {
            "valid": True,
            "title": ScannerHelpers.clean_text(title),
            "length": len(title),
            "word_count": len(title.split()),
        }

    @staticmethod
    def extract_volume_info(title: str) -> dict[str, Any]:
        """
        Extract volume information from title.
        """
        if not title:
            return {"volume": "", "volume_number": 0}

        # Common volume patterns
        volume_patterns = [
            r"vol\.?\s*(\d+(?:\.\d+)?)",
            r"v\s*(\d+(?:\.\d+)?)",
            r"volumen\s*(\d+(?:\.\d+)?)",
            r"tomo\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:vol|v|tomo|volumen)",
            r"capítulo\s*(\d+(?:\.\d+)?)",
        ]

        for pattern in volume_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                volume = match.group(1)
                return {"volume": f"Vol. {volume}", "volume_number": float(volume), "pattern_matched": pattern}

        return {"volume": "", "volume_number": 0}

    @staticmethod
    def normalize_tags(tags: list[str]) -> list[str]:
        """
        Normalize and clean tag list.
        """
        if not tags:
            return []

        normalized = []
        for tag in tags:
            if tag and isinstance(tag, str):
                clean_tag = ScannerHelpers.clean_text(tag)
                if clean_tag and len(clean_tag) >= 2:
                    normalized.append(clean_tag.lower())

        # Remove duplicates and sort
        return sorted(list(set(normalized)))

    @staticmethod
    def detect_special_chars(text: str) -> dict[str, Any]:
        """
        Detect special characters in text.
        """
        if not text:
            return {"has_special": False, "chars": []}

        special_chars = [
            ":",
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

        found_chars = [char for char in text if char in special_chars]

        return {
            "has_special": len(found_chars) > 0,
            "chars": found_chars,
            "char_count": len(found_chars),
            "clean_text": "".join([char for char in text if char not in special_chars]),
        }

    @staticmethod
    async def sync_taxonomy(session, model: Any, names: list[str]) -> list[Any]:
        """
        Sincroniza una lista de nombres con una tabla maestra (Genre o Demographic).
        Retorna la lista de objetos de la base de datos.
        """
        if not names:
            return []

        # Normalizar nombres
        clean_names = sorted(list(set(n.strip() for n in names if n and isinstance(n, str))))
        if not clean_names:
            return []

        # 1. Buscar existentes
        stmt = select(model).where(model.name.in_(clean_names))
        result = await session.execute(stmt)
        existing_objs = {obj.name: obj for obj in result.scalars().all()}

        final_objs = []
        for name in clean_names:
            if name in existing_objs:
                final_objs.append(existing_objs[name])
            else:
                # 2. Crear nuevos
                new_obj = model(name=name)
                session.add(new_obj)
                final_objs.append(new_obj)

        await session.flush()
        return final_objs

    @staticmethod
    def calculate_complexity_score(text: str) -> dict[str, Any]:
        """
        Calculate complexity score for text analysis.
        """
        if not text:
            return {"score": 0, "factors": []}

        factors = []

        # Length factor
        length_score = min(len(text) / 100, 1.0)
        factors.append(f"length: {length_score:.2f}")

        # Special characters factor
        special_chars = ScannerHelpers.detect_special_chars(text)
        special_score = special_chars["char_count"] * 0.1
        factors.append(f"special_chars: {special_score:.2f}")

        # Word diversity factor
        words = text.split()
        unique_words = len(set(words))
        diversity_score = min(unique_words / len(words), 1.0)
        factors.append(f"diversity: {diversity_score:.2f}")

        # Overall complexity
        total_score = (length_score + special_score + (1 - diversity_score)) / 3

        return {
            "score": total_score,
            "factors": factors,
            "complexity_level": "high" if total_score > 0.7 else "medium" if total_score > 0.4 else "low",
        }
