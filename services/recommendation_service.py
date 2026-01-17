import logging
import random
from typing import List, Dict, Any
from sqlalchemy import desc
from utils.library_db import get_session
from models.library_models import LocalBook
from core.db_manager import db_manager

logger = logging.getLogger(__name__)


class RecommendationService:
    @staticmethod
    async def get_recommendations(user_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Genera recomendaciones basadas en el historial de descargas.
        Estrategia:
        1. Obtener últimas 10 descargas.
        2. Extraer autores y tags frecuentes.
        3. Buscar libros que coincidan pero no estén descargados.
        4. Priorizar por Rating > Popularidad.
        """
        async with db_manager.connection() as conn:
            # 1. Obtener historial reciente (últimos 10)
            cursor = await conn.execute("""
                SELECT title, author, download_url
                FROM download_history
                WHERE user_id = ?
                ORDER BY downloaded_at DESC LIMIT 10
            """, (user_id,))
            history = await cursor.fetchall()

            # Obtener lista de IDs/Títulos ya descargados para excluir
            cursor = await conn.execute("SELECT title FROM download_history WHERE user_id = ?", (user_id,))
            downloaded_titles = {row[0] for row in await cursor.fetchall()}

        if not history:
            # Cold start: Recomendar los mejor valorados/populares
            return RecommendationService._get_popular_recommendations(limit, downloaded_titles)

        # 2. Analizar preferencias
        authors = {}
        # Simple extraction logic (could be improved with Tags if stored in history)
        for title, author, _ in history:
            if author and author != "Desconocido":
                authors[author] = authors.get(author, 0) + 1

        # Top authors
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:3]
        target_authors = [a[0] for a in top_authors]

        # 3. Buscar similares en LocalBook
        session = get_session()
        try:
            query = session.query(LocalBook).filter(
                LocalBook.title.notin_(downloaded_titles)
            )

            # Filtro por autor (OR logic)
            if target_authors:
                query = query.filter(LocalBook.author.in_(target_authors))

            # Ordenar por rating y luego random para variedad
            candidates = query.order_by(desc(LocalBook.rating_average)).limit(limit * 3).all()

            if not candidates:
                # Fallback to popular if no specific matches
                session.close()
                return RecommendationService._get_popular_recommendations(limit, downloaded_titles)

            # Shuffle and pick
            random.shuffle(candidates)
            selected = candidates[:limit]

            return [book.to_dict() for book in selected]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
        finally:
            session.close()

    @staticmethod
    def _get_popular_recommendations(limit: int, exclude_titles: set) -> List[Dict[str, Any]]:
        """Fallback: Libros más descargados de la biblioteca."""
        from core.db_manager import db_manager
        import asyncio
        
        session = get_session()
        try:
            # First try to get books by actual download count from download_history
            # We'll use a subquery approach to join with LocalBook
            from sqlalchemy import text
            
            # Query most downloaded book hashes from download_history
            result = session.execute(text("""
                SELECT lb.id, lb.title, lb.author, lb.cover_path, lb.rating_average, lb.rating_count,
                       lb.series, lb.volume, lb.content_hash
                FROM local_books lb
                LEFT JOIN (
                    SELECT book_hash, COUNT(*) as dl_count 
                    FROM download_history 
                    WHERE book_hash IS NOT NULL 
                    GROUP BY book_hash
                ) dh ON lb.content_hash = dh.book_hash
                WHERE lb.title NOT IN :exclude_titles OR :no_exclude = 1
                ORDER BY COALESCE(dh.dl_count, 0) DESC, lb.rating_average DESC, lb.rating_count DESC
                LIMIT :limit
            """), {"exclude_titles": tuple(exclude_titles) if exclude_titles else ('__NONE__',), 
                   "no_exclude": 1 if not exclude_titles else 0,
                   "limit": limit})
            
            books = result.fetchall()
            
            if books:
                return [
                    {
                        "id": row[0],
                        "title": row[1],
                        "author": row[2],
                        "cover_path": row[3],
                        "rating_average": row[4] or 0,
                        "rating_count": row[5] or 0,
                        "series": row[6],
                        "series_index": row[7],
                    }
                    for row in books
                ]
            
            # Fallback to simple rating-based query if no download history
            books = session.query(LocalBook).filter(
                LocalBook.title.notin_(exclude_titles) if exclude_titles else True
            ).order_by(desc(LocalBook.rating_average), desc(LocalBook.rating_count)).limit(limit).all()

            return [book.to_dict() for book in books]
        except Exception as e:
            logger.error(f"Error getting popular recommendations: {e}")
            # Ultimate fallback - just get any books
            books = session.query(LocalBook).limit(limit).all()
            return [book.to_dict() for book in books]
        finally:
            session.close()
