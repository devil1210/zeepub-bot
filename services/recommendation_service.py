import logging
import random
from datetime import date
from typing import Any

from sqlalchemy import String, case, cast, desc, or_, select

from core.db_manager_pg import pg_manager
from models.library_models import LocalBook, SeriesMetadata, UserDownload, UserRating

logger = logging.getLogger(__name__)


class RecommendationService:
    @staticmethod
    async def get_recommendations(user_id: int, limit: int = 4) -> list[dict[str, Any]]:
        """
        Genera recomendaciones de SERIES basadas en descargas y valoraciones.
        Cambia una vez al día por usuario. Regresa diccionarios listos para el Mini App.
        """
        try:
            downloaded_series_hashes = set()
            liked_series_hashes = set()

            async with pg_manager.get_session() as session:
                # 1. Obtener historial de descargas -> Extraer series_hash
                dl_stmt = (
                    select(LocalBook.series_hash)
                    .join(UserDownload, UserDownload.book_hash == LocalBook.book_hash)
                    .where(UserDownload.user_id == user_id)
                )
                dl_res = await session.execute(dl_stmt)
                downloaded_series_hashes = {row[0] for row in dl_res.fetchall() if row[0]}

                # 2. Valoraciones positivas -> Extraer series_hash
                rate_stmt = (
                    select(LocalBook.series_hash)
                    .join(UserRating, UserRating.book_hash == LocalBook.book_hash)
                    .where(UserRating.user_id == user_id, UserRating.rating >= 4)
                )
                rate_res = await session.execute(rate_stmt)
                liked_series_hashes = {row[0] for row in rate_res.fetchall() if row[0]}

                combined_hashes = downloaded_series_hashes.union(liked_series_hashes)

                if not combined_hashes:
                    return await RecommendationService._get_popular_recommendations(
                        user_id, session, limit, downloaded_series_hashes
                    )

                # 3. Analizar perfiles de Series (Tags y Autores)
                hist_stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash.in_(combined_hashes))
                hist_res = await session.execute(hist_stmt)
                history_series = hist_res.scalars().all()

                tags_freq = {}
                authors_freq = {}

                for s in history_series:
                    if s.author and s.author != "Desconocido":
                        authors_freq[s.author] = authors_freq.get(s.author, 0) + 2
                    if s.tags_json:
                        for t in s.tags_json:
                            tags_freq[t] = tags_freq.get(t, 0) + 1

                top_authors = sorted(authors_freq.items(), key=lambda x: x[1], reverse=True)[:3]
                top_tags = sorted(tags_freq.items(), key=lambda x: x[1], reverse=True)[:5]

                target_authors = [a[0] for a in top_authors]
                target_tags = [t[0] for t in top_tags]

                # 4. Buscar Series similares (excluyendo lo que ya descargó)
                cand_stmt = select(SeriesMetadata).where(SeriesMetadata.series_hash.notin_(downloaded_series_hashes))

                filters = []
                if target_authors:
                    filters.append(SeriesMetadata.author.in_(target_authors))

                if target_tags:
                    tag_filters = [cast(SeriesMetadata.tags_json, String).ilike(f"%{tag}%") for tag in target_tags]
                    filters.append(or_(*tag_filters))

                if filters:
                    cand_stmt = cand_stmt.where(or_(*filters))

                # Ordenar por rating y luego variedad
                cand_stmt = cand_stmt.order_by(
                    desc(SeriesMetadata.rating_average), desc(SeriesMetadata.rating_count)
                ).limit(limit * 6)

                cand_res = await session.execute(cand_stmt)
                candidates = cand_res.scalars().all()

                if not candidates:
                    return await RecommendationService._get_popular_recommendations(
                        user_id, session, limit, downloaded_series_hashes
                    )

                # Formatear como diccionarios compatibles con Mini App (Series Style)
                results = []
                for s in candidates:
                    results.append(
                        {
                            "id": f"series_{s.series_hash}",
                            "title": s.series_name,
                            "author": s.author,
                            "cover": s.cover_url or "/book-placeholder.jpg",
                            "is_folder": True,
                            "series_hash": s.series_hash,
                            "numBooks": s.book_count,
                            "book_count": s.book_count,
                            "rating_average": s.rating_average,
                            "book_type": s.book_type,
                            "tags": s.tags_json or [],
                        }
                    )

                # Semilla diaria
                daily_seed = f"{user_id}_{date.today().isoformat()}"
                r = random.Random(daily_seed)
                r.shuffle(results)

                return results[:limit]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            return await RecommendationService._get_popular_recommendations(user_id, None, limit, set())

    @staticmethod
    async def _get_popular_recommendations(
        user_id: int, session, limit: int, exclude_hashes: set
    ) -> list[dict[str, Any]]:
        """Fallback: Series populares si no hay historial."""

        async def execute_query(sess):
            query = select(SeriesMetadata)
            if exclude_hashes:
                query = query.where(SeriesMetadata.series_hash.notin_(exclude_hashes))

            query = query.order_by(
                desc(case((SeriesMetadata.cover_url.isnot(None), 1), else_=0)),
                desc(SeriesMetadata.rating_average),
                desc(SeriesMetadata.rating_count),
            ).limit(limit * 3)

            res = await sess.execute(query)
            return res.scalars().all()

        try:
            if session:
                series_list = await execute_query(session)
            else:
                async with pg_manager.get_session() as new_session:
                    series_list = await execute_query(new_session)

            results = []
            for s in series_list:
                results.append(
                    {
                        "id": f"series_{s.series_hash}",
                        "title": s.series_name,
                        "author": s.author,
                        "cover": s.cover_url or "/book-placeholder.jpg",
                        "is_folder": True,
                        "series_hash": s.series_hash,
                        "numBooks": s.book_count,
                        "book_count": s.book_count,
                        "rating_average": s.rating_average,
                        "book_type": s.book_type,
                        "tags": s.tags_json or [],
                    }
                )

            daily_seed = f"{user_id}_{date.today().isoformat()}"
            r = random.Random(daily_seed)
            r.shuffle(results)

            return results[:limit]
        except Exception as e:
            logger.error(f"Error getting popular recommendations: {e}")
            try:
                async with pg_manager.get_session() as last_resort:
                    stmt = select(SeriesMetadata).limit(limit)
                    res = await last_resort.execute(stmt)
                    series_list = res.scalars().all()
                    return [
                        {
                            "id": f"series_{s.series_hash}",
                            "title": s.series_name,
                            "is_folder": True,
                            "cover": s.cover_url,
                        }
                        for s in series_list
                    ]
            except Exception:
                return []
