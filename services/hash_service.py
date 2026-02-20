import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class HashService:
    """
    Servicio centralizado para la generación de hashes de libros y series.
    Garantiza consistencia absoluta en toda la aplicación.
    """

    @staticmethod
    def norm_string(s: Any, lowercase: bool = True) -> str:
        """Normaliza una cadena para generación de hashes."""
        if s is None:
            return ""
        s = str(s).strip()
        if lowercase:
            s = s.lower()
        return s

    @classmethod
    def generate_book_hash(
        cls,
        series: str | None = None,
        author: str | None = None,
        book_type: str | None = None,
        volume: Any | None = None,
        translator: str | None = None,
        layout_by: str | None = None,
        language: str | None = "es",
        edition: str | None = None,
        is_uncensored: int = 0,
        color_mode: str = "bw",
    ) -> str:
        """
        Genera un hash estable basado exclusivamente en:
        series + author + book_type + volume + translator + layout_by + language + edition + traits.
        NO usar title.
        """
        s_norm = cls.norm_string(series)
        a_norm = cls.norm_string(author)
        t_norm = cls.norm_string(book_type)

        # Normalización estricta de volumen para estabilidad del hash
        v_norm = ""
        if volume is not None:
            try:
                v_val = float(volume)
                if v_val == int(v_val):
                    v_norm = str(int(v_val))
                else:
                    v_norm = str(v_val)
            except (ValueError, TypeError):
                v_norm = cls.norm_string(volume)

        tr_norm = cls.norm_string(translator)
        l_norm = cls.norm_string(layout_by)
        lang_norm = cls.norm_string(language or "es")
        ed_norm = cls.norm_string(edition)

        # Normalizar edición para evitar duplicidad con is_uncensored y color_mode
        # Esto asegura que "Color" como tag o como property generen el mismo hash
        if ed_norm:
            import re

            # Lista de términos redundantes a eliminar de la cadena de edición
            # (Ya están representados en las flags is_uncensored y color_mode)
            redundant = [
                r"ilustraciones a color",
                r"full color",
                r"color",
                r"sin censura",
                r"uncensored",
                r"no censura",
                r"blanco y negro",
                r"b&w",
                r"b&n",
                r"grayscale",
                r"b/n",
            ]
            for pattern in redundant:
                ed_norm = re.sub(rf"\b{pattern}\b", "", ed_norm, flags=re.IGNORECASE)
            # Limpiar espacios extra resultantes
            ed_norm = " ".join(ed_norm.split()).strip()

        # Cadena de identidad determinista según especificación estricta del usuario
        # trans/layout/lang/edition names used here must match previous usage to avoid hash drift
        identity = (
            f"series:{s_norm}|author:{a_norm}|type:{t_norm}|vol:{v_norm}|"
            f"trans:{tr_norm}|layout:{l_norm}|lang:{lang_norm}|edition:{ed_norm}|"
            f"uncensored:{is_uncensored}|color:{color_mode}"
        )

        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    @classmethod
    def generate_series_hash(cls, series: str, author: str | None = None, book_type: str | None = None) -> str:
        """
        Genera un hash estable para la serie basado en: series + author + book_type.
        """
        s_norm = cls.norm_string(series)
        a_norm = cls.norm_string(author)
        t_norm = cls.norm_string(book_type)

        identity = f"series:{s_norm}|author:{a_norm}|type:{t_norm}"

        return hashlib.sha256(identity.encode("utf-8")).hexdigest()


hash_service = HashService()
