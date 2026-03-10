"""
services/v4/ai/metadata_swarm.py
----------------------------------
MetadataSwarm V4: Sub-agente de IA responsable de la clasificación
automática de EPUBs sin necesidad de intervención manual.

Orquesta llamadas a AIService para:
  1. analyze_book()       — normaliza metadatos de un EPUB recién subido
  2. check_duplicates()   — detecta series duplicadas por texto/hash
  3. match_existing_series() — vincula un libro nuevo a una serie existente

No escribe en la BD directamente; devuelve propuestas que el
UploadHandler o el IngestionService aplican tras validación.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BookProposal:
    """
    Propuesta de metadatos generada por AI para un EPUB nuevo.
    El handler decide si aplicarla directamente o ponerla en revisión.
    """

    series_english: str = ""
    series_spanish: str = ""
    volume: float = 0.0
    group_siglas: str = ""
    group_full: str = ""
    suggested_filename: str = ""
    book_type: str = "novel"
    genres: list[str] = field(default_factory=list)
    demographics: list[str] = field(default_factory=list)
    description: str = ""
    confidence: float = 0.0
    is_uncensored: bool = False
    color_mode: str = "bw"
    raw_response: dict = field(default_factory=dict)


@dataclass
class DuplicateReport:
    """Reporte de duplicados potenciales en la biblioteca."""

    has_duplicates: bool = False
    pairs: list[dict] = field(default_factory=list)
    total_checked: int = 0


class MetadataSwarm:
    """
    Sub-agente de clasificación automática de metadatos.
    Orquesta llamadas a AIService.normalize_book_metadata y
    AIService.analyze_potential_merge.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    #  Análisis de un EPUB individual                                      #
    # ------------------------------------------------------------------ #

    async def analyze_book(self, book_data: dict[str, Any]) -> BookProposal:
        """
        Analiza un EPUB recién subido y propone metadatos normalizados.

        Args:
            book_data: dict con al menos 'filename' y 'raw_metadata'
                       (los que extrae el parser EPUB interno).

        Returns:
            BookProposal con los metadatos sugeridos por Gemini.
        """
        from services.ai_service import AIService

        filename: str = book_data.get("filename", "unknown.epub")
        raw_meta: dict = book_data.get("raw_metadata", {})

        # Enriquecer raw_meta con datos del título/autor si vienen aparte
        if book_data.get("title"):
            raw_meta.setdefault("title", book_data["title"])
        if book_data.get("author"):
            raw_meta.setdefault("creator", book_data["author"])

        self.logger.info(f"[SWARM] Analizando: {filename}")

        try:
            result = await AIService.normalize_book_metadata(filename, raw_meta)
        except Exception as e:
            self.logger.error(f"[SWARM] Fallo AI para {filename}: {e}")
            result = None

        if not result:
            self.logger.warning(f"[SWARM] Sin respuesta de AI para {filename}. Usando propuesta vacía.")
            return BookProposal(
                series_english=raw_meta.get("title", filename),
                suggested_filename=filename,
                raw_response={},
            )

        proposal = BookProposal(
            series_english=result.get("series_english", ""),
            series_spanish=result.get("series_spanish", ""),
            volume=float(result.get("volume") or 0.0),
            group_siglas=result.get("group_siglas", ""),
            group_full=result.get("group_full", ""),
            suggested_filename=result.get("suggested_filename", filename),
            book_type=result.get("book_type", "novel"),
            genres=result.get("genres") or [],
            demographics=result.get("demographics") or [],
            description=result.get("cleaned_description", ""),
            confidence=float(result.get("confidence") or 0.0),
            is_uncensored=bool(result.get("is_uncensored", False)),
            color_mode=result.get("color_mode", "bw"),
            raw_response=result,
        )

        self.logger.info(
            f"[SWARM] Propuesta → '{proposal.series_spanish}' Vol.{proposal.volume} conf={proposal.confidence:.0%}"
        )
        return proposal

    # ------------------------------------------------------------------ #
    #  Detección de duplicados                                             #
    # ------------------------------------------------------------------ #

    async def check_duplicates(self, db_series: list[dict]) -> DuplicateReport:
        """
        Analiza una lista de series de la BD y detecta pares potencialmente
        duplicados usando AIService.analyze_potential_merge.

        Args:
            db_series: Lista de dicts con 'series_name', 'author', 'book_count', 'series_hash'.

        Returns:
            DuplicateReport con los pares sospechosos.
        """
        from services.ai_service import AIService

        if len(db_series) < 2:
            return DuplicateReport(total_checked=len(db_series))

        self.logger.info(f"[SWARM] Verificando duplicados en {len(db_series)} series...")

        pairs: list[dict] = []
        total_checked = 0

        # Comparación O(n²) con early-stop por confianza.
        # Para listas grandes, usar prefiltrado por autor/inicial antes de llamar a AI.
        for i, series_a in enumerate(db_series):
            for series_b in db_series[i + 1 :]:
                # Heurística rápida: si los nombres empiezan igual, vale la pena preguntar a AI
                name_a = (series_a.get("series_name") or "").lower()
                name_b = (series_b.get("series_name") or "").lower()

                if not self._worth_checking(name_a, name_b):
                    continue

                total_checked += 1
                try:
                    result = await AIService.analyze_potential_merge(series_a, series_b)
                    if result and result.get("is_same") and result.get("confidence", 0) > 0.85:
                        pairs.append(
                            {
                                "series_a": series_a,
                                "series_b": series_b,
                                "confidence": result["confidence"],
                                "reason": result.get("reason", ""),
                                "suggested_main": result.get("suggested_main_name", ""),
                            }
                        )
                        self.logger.info(
                            f"[SWARM DUPE] '{series_a['series_name']}' ≈ "
                            f"'{series_b['series_name']}' conf={result['confidence']:.0%}"
                        )
                except Exception as e:
                    self.logger.warning(f"[SWARM] Error al comparar series: {e}")

        self.logger.info(f"[SWARM] Duplicados: {len(pairs)} pares sospechosos de {total_checked} comparaciones")
        return DuplicateReport(
            has_duplicates=len(pairs) > 0,
            pairs=pairs,
            total_checked=total_checked,
        )

    # ------------------------------------------------------------------ #
    #  Vincular a serie existente                                          #
    # ------------------------------------------------------------------ #

    async def match_existing_series(
        self,
        proposal: BookProposal,
        candidate_series: list[dict],
    ) -> dict | None:
        """
        Dado un BookProposal y una lista de series candidatas de la BD,
        usa AIService.analyze_potential_merge para encontrar la mejor.
        Devuelve la serie coincidente o None si no hay match.
        """
        from services.ai_service import AIService

        if not candidate_series:
            return None

        book_as_series = {
            "series_name": proposal.series_english or proposal.series_spanish,
            "author": proposal.group_full,
            "book_count": 1,
        }

        for candidate in candidate_series[:10]:  # Limitar a 10 candidates
            try:
                result = await AIService.analyze_potential_merge(book_as_series, candidate)
                if result and result.get("is_same") and result.get("confidence", 0) > 0.85:
                    self.logger.info(
                        f"[SWARM MATCH] Vinculando a '{candidate.get('series_name')}' conf={result['confidence']:.0%}"
                    )
                    return candidate
            except Exception as e:
                self.logger.warning(f"[SWARM] Error en match_existing_series: {e}")

        return None

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _worth_checking(name_a: str, name_b: str) -> bool:
        """
        Heurística barata para decidir si vale la pena llamar a la IA.
        Evita comparar series obviamente distintas.
        """
        if not name_a or not name_b:
            return False
        # Comparten al menos 4 caracteres iniciales → posible duplicado
        return name_a[:4] == name_b[:4] or _similarity_score(name_a, name_b) > 0.75


def _similarity_score(a: str, b: str) -> float:
    """Jaccard similarity de bigramas para pre-filtro rápido."""

    def bigrams(s: str) -> set:
        return {s[i : i + 2] for i in range(len(s) - 1)}

    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)
