import logging
import random
from datetime import date
from typing import Any, Dict, List

from sqlalchemy import desc, or_, select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, UserDownload, UserRating

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

            async with pg_manager.get_session() as session:
                # 1. Obtener historial de descargas
                dl_stmt = select(UserDownload.book_hash).where(UserDownload.user_id == user_id)
                dl_res = await session.execute(dl_stmt)
                downloaded_hashes = {row[0] for row in dl_res.fetchall() if row[0]}

                # 2. Obtener valoraciones positivas (>= 4 estrellas)
                # UserRating has book_hash
                rate_stmt = select(UserRating.book_hash).where(
                    UserRating.user_id == user_id, 
                    UserRating.rating >= 4
                )
                rate_res = await session.execute(rate_stmt)
                liked_hashes = {row[0] for row in rate_res.fetchall() if row[0]}

                combined_hashes = downloaded_hashes.union(liked_hashes)

                if not combined_hashes:
                    return await RecommendationService._get_popular_recommendations(user_id, session, limit, downloaded_hashes)

                # 3. Analizar perfiles (Tags y Autores)
                hist_stmt = select(LocalBook).where(LocalBook.book_hash.in_(combined_hashes))
                hist_res = await session.execute(hist_stmt)
                history_books = hist_res.scalars().all()

                tags_freq = {}
                authors_freq = {}

                for b in history_books:
                    if b.author and b.author != "Desconocido":
                        authors_freq[b.author] = authors_freq.get(b.author, 0) + 2 # Peso autores
                    if b.tags:
                        for t in b.tags:
                            tags_freq[t] = tags_freq.get(t, 0) + 1

                # Top de cada uno
                top_authors = sorted(authors_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                top_tags = sorted(tags_freq.items(), key=lambda x: x[1], reverse=True)[:5]

                target_authors = [a[0] for a in top_authors]
                target_tags = [t[0] for t in top_tags]

                # 4. Buscar similares
                cand_stmt = select(LocalBook).where(LocalBook.book_hash.notin_(downloaded_hashes))

                # Construir filtros dinámicos (OR de autores o tags)
                filters = []
                if target_authors:
                    filters.append(LocalBook.author.in_(target_authors))
                
                if target_tags:
                    # tags is JSONB in Postgres usually, or if it's text we use like
                    # LocalBook.tags is JSON (Column(JSON))
                    # In Postgres, we can use JSONB containment or just cast to string for simplicity if it varies
                    tag_filters = [LocalBook.tags.astext.ilike(f"%{tag}%") for tag in target_tags]
                    filters.append(or_(*tag_filters))

                if filters:
                    cand_stmt = cand_stmt.where(or_(*filters))

                # Ordenar por rating y luego variedad
                cand_stmt = cand_stmt.order_by(
                    desc(LocalBook.rating_average), 
                    desc(LocalBook.rating_count)
                ).limit(limit * 6)

                cand_res = await session.execute(cand_stmt)
                candidates = cand_res.scalars().all()

                if not candidates:
                    return await RecommendationService._get_popular_recommendations(user_id, session, limit, downloaded_hashes)

                results = [book.to_dict() for book in candidates]
                
                # Semilla diaria por usuario
                daily_seed = f"{user_id}_{date.today().isoformat()}"
                r = random.Random(daily_seed)
                r.shuffle(results)
                
                return results[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return await RecommendationService._get_popular_recommendations(user_id, None, limit, set())

    @staticmethod
    async def _get_popular_recommendations(user_id: int, session, limit: int, exclude_hashes: set) -> List[Dict[str, Any]]:
        """Fallback: Libros populares del catálogo total si no hay historial."""
        
        async def execute_query(sess):
            query = select(LocalBook)
            if exclude_hashes:
                query = query.where(LocalBook.book_hash.notin_(exclude_hashes))
            
            # Priorizar libros con miniatura y buen rating
            query = query.order_by(
                desc(LocalBook.cover_low != None),
                desc(LocalBook.rating_average), 
                desc(LocalBook.rating_count)
            ).limit(limit * 3)

            res = await sess.execute(query)
            return res.scalars().all()

        try:
            if session:
                books = await execute_query(session)
            else:
                async with pg_manager.get_session() as new_session:
                    books = await execute_query(new_session)

            results = [book.to_dict() for book in books]
            
            daily_seed = f"{user_id}_{date.today().isoformat()}"
            r = random.Random(daily_seed)
            r.shuffle(results)
            
            return results[:limit]
        except Exception as e:
            logger.error(f"Error getting popular recommendations: {e}")
            # Super fallback
            try:
                 async with pg_manager.get_session() as last_resort:
                    stmt = select(LocalBook).limit(limit)
                    res = await last_resort.execute(stmt)
                    books = res.scalars().all()
                    return [book.to_dict() for book in books]
            except:
                return []
