import logging
import random
from datetime import date
from typing import List, Dict, Any
from sqlalchemy import desc, or_
from utils.library_db import get_session
from models.library_models import LocalBook
from core.metrics_db import metrics_db

logger = logging.getLogger(__name__)

class RecommendationService:
    @staticmethod
    async def get_recommendations(user_id: int, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones basadas en descargas y valoraciones.
        Cambia una vez al día por usuario.
        """
        try:
            downloaded_hashes = set()
            liked_hashes = set()

            # 1. Obtener historial de descargas y valoraciones desde metrics_db
            async with metrics_db.connection() as conn:
                # Descargas
                cursor = await conn.execute(
                    "SELECT content_hash FROM user_downloads WHERE user_id = ?", (user_id,)
                )
                downloaded_hashes = {row[0] for row in await cursor.fetchall() if row[0]}

                # Valoraciones positivas (>= 4 estrellas)
                cursor = await conn.execute(
                    "SELECT content_hash FROM user_ratings WHERE user_id = ? AND rating >= 4", (user_id,)
                )
                liked_hashes = {row[0] for row in await cursor.fetchall() if row[0]}

            combined_hashes = downloaded_hashes.union(liked_hashes)

            if not combined_hashes:
                return await RecommendationService._get_popular_recommendations(user_id, limit, downloaded_hashes)

            # 2. Analizar perfiles (Tags y Autores)
            session = get_session()
            try:
                history_books = session.query(LocalBook).filter(
                    LocalBook.content_hash.in_(combined_hashes)
                ).all()

                tags_freq = {}
                authors_freq = {}

                for b in history_books:
                    if b.author and b.author != "Desconocido":
                        authors_freq[b.author] = authors_freq.get(b.author, 0) + 2 # Peso autores
                    if b.tags:
                        for t in b.tags:
                            tags_freq[t] = tags_freq.get(t, 0) + 1

                # Top 3 de cada uno
                top_authors = sorted(authors_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                top_tags = sorted(tags_freq.items(), key=lambda x: x[1], reverse=True)[:5]

                target_authors = [a[0] for a in top_authors]
                target_tags = [t[0] for t in top_tags]

                # 3. Buscar similares
                query = session.query(LocalBook).filter(
                    LocalBook.content_hash.notin_(downloaded_hashes)
                )

                # Construir filtros dinámicos (OR de autores o tags)
                filters = []
                if target_authors:
                    filters.append(LocalBook.author.in_(target_authors))
                
                if target_tags:
                    tag_filters = [LocalBook.tags.like(f"%{tag}%") for tag in target_tags]
                    filters.append(or_(*tag_filters))

                if filters:
                    query = query.filter(or_(*filters))

                # Ordenar por rating y luego variedad
                candidates = query.order_by(
                    desc(LocalBook.rating_average), 
                    desc(LocalBook.rating_count)
                ).limit(limit * 6).all()

                if not candidates:
                    return await RecommendationService._get_popular_recommendations(user_id, limit, downloaded_hashes)

                # Convert to dicts first to avoid session issues after shuffle
                results = [book.to_dict() for book in candidates]
                
                # Semilla diaria por usuario para que no cambie en cada carga
                daily_seed = f"{user_id}_{date.today().isoformat()}"
                r = random.Random(daily_seed)
                r.shuffle(results)
                
                return results[:limit]

            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return await RecommendationService._get_popular_recommendations(user_id, limit, set())

    @staticmethod
    async def _get_popular_recommendations(user_id: int, limit: int, exclude_hashes: set) -> List[Dict[str, Any]]:
        """Fallback: Libros populares del catálogo total si no hay historial."""
        session = get_session()
        try:
            query = session.query(LocalBook)
            if exclude_hashes:
                query = query.filter(LocalBook.content_hash.notin_(exclude_hashes))
            
            # Priorizar libros con miniatura y buen rating
            books = query.order_by(
                desc(LocalBook.cover_thumb_path != None),
                desc(LocalBook.rating_average), 
                desc(LocalBook.rating_count)
            ).limit(limit * 3).all()

            results = [book.to_dict() for book in books]
            
            # Semilla diaria por usuario
            daily_seed = f"{user_id}_{date.today().isoformat()}"
            r = random.Random(daily_seed)
            r.shuffle(results)
            
            return results[:limit]
        except Exception as e:
            logger.error(f"Error getting popular recommendations: {e}")
            books = session.query(LocalBook).limit(limit).all()
            return [book.to_dict() for book in books]
        finally:
            session.close()

