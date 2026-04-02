# api/routes/agent_routes.py
#
# Rutas del Puente Agente (MCP Bridge)
# Expone endpoints para que SPbot (Node.js) pueda consultar Zeepub en tiempo real.
#
# Endpoints:
#   GET  /health            → Estado del servidor (uptime, versión)
#   GET  /api/search        → Búsqueda en catálogo (series, libros, autores, traductores)
#   GET  /api/stats         → Estadísticas globales del catálogo
#
# Autenticación: Header X-API-Key (configurado en AGENT_API_KEY en .env)

import logging
import os
import time

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import func, select

from core.database import async_session
from models.library import LocalBook, SeriesMetadata

logger = logging.getLogger(__name__)

# Tiempo de inicio del servidor (para calcular uptime)
_START_TIME = time.time()

# API Key de acceso interno (SPbot → Zeepub). Vacío = sin autenticación.
_AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")


def _verify_key(x_api_key: str | None):
    """Verifica la API Key del agente si está configurada."""
    if _AGENT_API_KEY and x_api_key != _AGENT_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: API Key inválida")


class AgentRoutes:
    """
    Rutas del puente MCP para el agente SP-Agent (SPbot).
    Single Responsibility: Exponer datos del catálogo al agente de Telegram.
    """

    def __init__(self):
        self.router = APIRouter(tags=["agent-bridge"])

    def get_router(self) -> APIRouter:
        return self.router

    # ── /health ───────────────────────────────────────────────────────────────

    async def health(self, x_api_key: str | None = Header(default=None)):
        """Estado del servidor Zeepub."""
        _verify_key(x_api_key)
        uptime_seconds = int(time.time() - _START_TIME)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return {
            "status": "ok",
            "uptime": f"{hours}h {minutes}m {seconds}s",
            "version": "zeepub-bot/1.0",
        }

    # ── /api/search ───────────────────────────────────────────────────────────

    async def search(
        self,
        q: str = Query(..., description="Término de búsqueda"),
        type: str = Query("serie", description="Tipo: serie | libro | autor | maquetador | traductor"),
        limit: int = Query(5, ge=1, le=20, description="Máximo de resultados"),
        x_api_key: str | None = Header(default=None),
    ):
        """Búsqueda en el catálogo de Zeepub."""
        _verify_key(x_api_key)
        pattern = f"%{q}%"

        try:
            async with async_session() as session:
                results = []

                if type in ("serie", "autor"):
                    # Buscar en tabla series
                    stmt = (
                        select(
                            SeriesMetadata.series_name,
                            SeriesMetadata.series_spanish,
                            SeriesMetadata.series_english,
                            SeriesMetadata.author,
                            SeriesMetadata.description,
                        )
                        .where(
                            (SeriesMetadata.series_name.ilike(pattern))
                            | (SeriesMetadata.series_spanish.ilike(pattern))
                            | (SeriesMetadata.series_english.ilike(pattern))
                            | (SeriesMetadata.author.ilike(pattern))
                        )
                        .limit(limit)
                    )
                    rows = (await session.execute(stmt)).fetchall()
                    for row in rows:
                        results.append(
                            {
                                "name": row.series_spanish or row.series_english or row.series_name,
                                "author": row.author,
                                "description": (row.description or "")[:200] if row.description else None,
                            }
                        )

                elif type == "libro":
                    stmt = (
                        select(LocalBook.title, LocalBook.author, LocalBook.layout_by, LocalBook.translator)
                        .where(LocalBook.title.ilike(pattern))
                        .limit(limit)
                    )
                    rows = (await session.execute(stmt)).fetchall()
                    for row in rows:
                        results.append(
                            {
                                "name": row.title,
                                "author": row.author,
                                "maquetador": row.layout_by,
                                "traductor": row.translator,
                            }
                        )

                elif type == "maquetador":
                    stmt = (
                        select(LocalBook.layout_by, func.count(LocalBook.id).label("count"))
                        .where(LocalBook.layout_by.ilike(pattern))
                        .group_by(LocalBook.layout_by)
                        .order_by(func.count(LocalBook.id).desc())
                        .limit(limit)
                    )
                    rows = (await session.execute(stmt)).fetchall()
                    for row in rows:
                        results.append({"name": row.layout_by, "book_count": row.count})

                elif type == "traductor":
                    stmt = (
                        select(LocalBook.translator, func.count(LocalBook.id).label("count"))
                        .where(LocalBook.translator.ilike(pattern))
                        .group_by(LocalBook.translator)
                        .order_by(func.count(LocalBook.id).desc())
                        .limit(limit)
                    )
                    rows = (await session.execute(stmt)).fetchall()
                    for row in rows:
                        results.append({"name": row.translator, "book_count": row.count})

                return {"query": q, "type": type, "results": results}

        except Exception as e:
            logger.error(f"[AgentRoutes] Error en búsqueda: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}") from e

    # ── /api/stats ────────────────────────────────────────────────────────────

    async def stats(self, x_api_key: str | None = Header(default=None)):
        """Estadísticas globales del catálogo de Zeepub."""
        _verify_key(x_api_key)
        try:
            async with async_session() as session:
                total_books = (await session.execute(select(func.count(LocalBook.id)))).scalar() or 0
                total_series = (await session.execute(select(func.count(SeriesMetadata.id)))).scalar() or 0

                # Maquetadores únicos
                maq_stmt = select(func.count(func.distinct(LocalBook.layout_by))).where(
                    LocalBook.layout_by.isnot(None), LocalBook.layout_by != ""
                )
                total_maquetadores = (await session.execute(maq_stmt)).scalar() or 0

                # Traductores únicos
                trad_stmt = select(func.count(func.distinct(LocalBook.translator))).where(
                    LocalBook.translator.isnot(None), LocalBook.translator != ""
                )
                total_traductores = (await session.execute(trad_stmt)).scalar() or 0

                return {
                    "total_books": total_books,
                    "total_series": total_series,
                    "total_maquetadores": total_maquetadores,
                    "total_traductores": total_traductores,
                }

        except Exception as e:
            logger.error(f"[AgentRoutes] Error en stats: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error obteniendo stats: {str(e)}") from e

    # ── Registro de rutas ─────────────────────────────────────────────────────

    def register_routes(self):
        """Registra los endpoints en el router FastAPI."""
        self.router.add_api_route(
            "/health",
            self.health,
            methods=["GET"],
            summary="Health check del servidor Zeepub",
        )
        self.router.add_api_route(
            "/api/search",
            self.search,
            methods=["GET"],
            summary="Búsqueda en el catálogo de Zeepub",
        )
        self.router.add_api_route(
            "/api/stats",
            self.stats,
            methods=["GET"],
            summary="Estadísticas globales del catálogo",
        )
