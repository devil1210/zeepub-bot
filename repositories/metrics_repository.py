import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Repositorio centralizado para descargas y valoraciones basadas en hashes."""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    # --- Downloads ---

    async def add_download(self, user_id: int, content_hash: str, series_hash: Optional[str] = None, title: Optional[str] = None):
        async with self.db_manager.connection() as conn:
            await conn.execute(
                "INSERT INTO user_downloads (user_id, content_hash, series_hash, title) VALUES (?, ?, ?, ?)",
                (user_id, content_hash, series_hash, title)
            )
            await conn.commit()

    async def has_downloaded(self, user_id: int, content_hash: str) -> bool:
        if not content_hash:
            return False
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT 1 FROM user_downloads WHERE user_id = ? AND content_hash = ? LIMIT 1",
                (user_id, content_hash)
            )
            return await cursor.fetchone() is not None

    async def get_total_downloads(self, content_hash: str) -> int:
        if not content_hash:
            return 0
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM user_downloads WHERE content_hash = ?",
                (content_hash,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_series_downloads(self, series_hash: str) -> int:
        if not series_hash:
            return 0
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM user_downloads WHERE series_hash = ?",
                (series_hash,)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    # --- Ratings ---

    async def add_rating(self, user_id: int, content_hash: str, rating: int):
        async with self.db_manager.connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_ratings (user_id, content_hash, rating, rated_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, content_hash) DO UPDATE SET 
                    rating = excluded.rating,
                    rated_at = CURRENT_TIMESTAMP
                """,
                (user_id, content_hash, rating)
            )
            await conn.commit()

    async def get_rating_stats(self, content_hash: str) -> Dict[str, Any]:
        if not content_hash:
            return {"average": 0.0, "count": 0}
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT AVG(rating), COUNT(*) FROM user_ratings WHERE content_hash = ?",
                (content_hash,)
            )
            row = await cursor.fetchone()
            return {
                "average": round(row[0], 1) if row and row[0] else 0.0,
                "count": row[1] if row else 0
            }

    async def get_series_rating_stats(self, series_hash: str) -> Dict[str, Any]:
        """Calcula el promedio y conteo de ratings de todos los libros de una serie."""
        if not series_hash:
            return {"average": 0.0, "count": 0}

        # Necesitamos unir con la tabla de libros para saber qué hashes pertenecen a la serie
        # Pero podemos simplificarlo si guardamos series_hash en user_ratings también.
        # Por ahora lo haremos vía JOIN indirecto o asumiendo que el buscador ya nos da los hashes.
        return {"average": 0.0, "count": 0}  # Placeholder until series link is established

# Singleton
from core.metrics_db import metrics_db
metrics_repo = MetricsRepository(metrics_db)
