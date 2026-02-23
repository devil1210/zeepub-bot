# services/metadata_service.py
"""
Servicio de metadatos - ahora delega a repositorios locales y metadata_orchestrator.
Las funciones OPDS han sido eliminadas.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def get_sinopsis_from_series(series_hash: str) -> str | None:
    """Obtiene la sinopsis desde SeriesMetadata en la BD local."""
    from repositories.series_repository import series_repo

    try:
        series = await series_repo.get_by_hash(series_hash)
        if series:
            desc = getattr(series, "description", None)
            if desc:
                return str(desc)
    except Exception as e:
        logger.debug(f"Error obteniendo sinopsis de BD: {e}")
    return None


async def get_series_metadata(series_hash: str) -> dict[str, Any]:
    """Obtiene metadata completa de una serie desde la BD local."""
    from repositories.series_repository import series_repo

    try:
        series = await series_repo.get_by_hash(series_hash)
        if series:
            return series.to_dict()
    except Exception as e:
        logger.debug(f"Error obteniendo metadata de serie: {e}")
    return {}
