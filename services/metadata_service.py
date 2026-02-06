# services/metadata_service.py

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def obtener_sinopsis_opds(series_id: str) -> str | None:
    """Obtiene la sinopsis de una serie desde OPDS (DESACTIVADO)."""
    return None


async def obtener_sinopsis_opds_volumen(series_id: str, volume_id: str) -> str | None:
    """Obtiene la sinopsis específica de un volumen (DESACTIVADO)."""
    return None


async def obtener_metadatos_opds(series_id: str, volume_id: str) -> dict[str, Any]:
    """Extrae metadatos desde OPDS (DESACTIVADO)."""
    return {
        "titulo_serie": None,
        "titulo_volumen": None,
        "autor": None,
        "ilustrador": None,
        "generos": [],
        "tags": [],
        "categoria": None,
        "demografia": None,
        "fecha_publicacion": None,
    }
