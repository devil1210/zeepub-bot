import logging

from sqlalchemy import select, text

from core.db_manager_pg import pg_manager
from models.library_models import Series
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class SemanticService:
    """
    Servicio de búsqueda semántica y RAG.
    Maneja la generación de embeddings y la recuperación por similitud de cosenos.
    """

    @staticmethod
    async def update_index(force: bool = False):
        """
        Calcula embeddings para todas las series que no lo tengan.
        """
        logger.info(f"🔍 Iniciando actualización de índice semántico (force={force})...")
        stats = {"updated": 0, "errors": 0, "skipped": 0}

        async with pg_manager.get_session() as session:
            # Buscar series sin embedding (o todas si force=True)
            if force:
                query = select(Series)
            else:
                query = select(Series).where(Series.embedding.is_(None))

            result = await session.execute(query)
            series_list = result.scalars().all()

            if not series_list:
                logger.info("✅ No hay series pendientes de indexación.")
                return stats

            for s in series_list:
                try:
                    # Combinar título y descripción para el embedding
                    text_to_embed = f"{s.title_raw}\n{s.title_spanish or ''}\n{s.description or ''}".strip()
                    if not text_to_embed:
                        stats["skipped"] += 1
                        continue

                    embedding = await AIService.get_embedding(text_to_embed)
                    if embedding:
                        s.embedding = embedding
                        stats["updated"] += 1
                        logger.info(f"✨ Embedding generado para: {s.title_raw}")
                    else:
                        stats["errors"] += 1
                        logger.error(f"❌ Falló generación de embedding para: {s.title_raw}")

                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"❌ Error procesando serie {s.id}: {e}")

            await session.commit()

        logger.info(f"📊 Resumen de indexación: {stats}")
        return stats

    @staticmethod
    async def search(query_text: str, limit: int = 5):
        """
        Busca series por similitud semántica.
        Utiliza el operador <=> de pgvector (distancia de coseno).
        """
        logger.info(f"🔍 Buscando: '{query_text}'")

        query_embedding = await AIService.get_embedding(query_text)
        if not query_embedding:
            return []

        async with pg_manager.get_session() as session:
            # Usar SQL crudo para pgvector si SQLAlchemy no tiene soporte directo instalado
            # El operador <=> devuelve la distancia de coseno (menor es más similar)
            sql = text("""
                SELECT id, title_raw, title_spanish, slug,
                       (embedding <=> :embedding) as distance
                FROM series
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :embedding
                LIMIT :limit
            """)

            params = {
                "embedding": str(query_embedding),  # pgvector espera string o lista decorada
                "limit": limit,
            }

            result = await session.execute(sql, params)
            rows = result.fetchall()

            search_results = []
            for r in rows:
                search_results.append(
                    {
                        "id": str(r.id),
                        "title": r.title_spanish or r.title_raw,
                        "slug": r.slug,
                        "similarity": round(1 - r.distance, 4),  # Convertir distancia a similitud
                    }
                )

            return search_results


# Instancia global
semantic_service = SemanticService()
