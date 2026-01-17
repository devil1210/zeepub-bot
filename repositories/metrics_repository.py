import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Repositorio centralizado para descargas y valoraciones basadas en hashes."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        from core.supabase_manager import supabase_manager
        self.supabase = supabase_manager
    # --- Downloads ---

    async def add_download(
        self,
        user_id: int,
        content_hash: str,
        series_hash: Optional[str] = None,
        title: Optional[str] = None,
    ):
        if self.supabase.is_active:
            try:
                data = {
                    "user_id": user_id,
                    "content_hash": content_hash,
                    "series_hash": series_hash,
                    "title": title
                }
                self.supabase.get_client().table('user_downloads').insert(data).execute()
            except Exception as e:
                logger.error(f"Supabase metrics add_download error: {e}")

        async with self.db_manager.connection() as conn:
            await conn.execute(
                "INSERT INTO user_downloads (user_id, content_hash, series_hash, title) VALUES (?, ?, ?, ?)",
                (user_id, content_hash, series_hash, title),
            )
            await conn.commit()

    async def has_downloaded(self, user_id: int, content_hash: str) -> bool:
        if not content_hash:
            return False
        
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_downloads').select("id").eq('user_id', user_id).eq('content_hash', content_hash).limit(1).execute()
                if res.data: return True
            except Exception as e:
                logger.error(f"Supabase metrics has_downloaded error: {e}")

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT 1 FROM user_downloads WHERE user_id = ? AND content_hash = ? LIMIT 1",
                (user_id, content_hash),
            )
            return await cursor.fetchone() is not None

    async def get_total_downloads(self, content_hash: str) -> int:
        if not content_hash:
            return 0
        
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_downloads').select("id", count='exact').eq('content_hash', content_hash).execute()
                return res.count or 0
            except Exception as e:
                logger.error(f"Supabase metrics get_total_downloads error: {e}")

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM user_downloads WHERE content_hash = ?",
                (content_hash,),
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_series_downloads(self, series_hash: str) -> int:
        if not series_hash:
            return 0
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM user_downloads WHERE series_hash = ?",
                (series_hash,),
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_total_downloads_by_hashes(self, hashes: List[str]) -> int:
        """Calcula el total de descargas para una lista de series_hash o content_hash."""
        if not hashes:
            return 0

        # SQL con placeholders dinámicos
        placeholders = ",".join(["?"] * len(hashes))
        query = f"SELECT COUNT(*) FROM user_downloads WHERE series_hash IN ({placeholders}) OR content_hash IN ({placeholders})"
        # Duplicamos la lista porque la usamos dos veces en el WHERE
        params = hashes + hashes

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(query, params)
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_source_downloads(self, source_id: int) -> int:
        """Calcula el total de descargas de todos los libros de una fuente específica."""
        # Necesitamos saber qué series_hash o content_hash pertenecen a la fuente.
        # Por simplicidad y eficiencia, consultaremos la tabla local_books vía JOIN o subquery.
        async with self.db_manager.connection() as conn:
            # Nota: user_downloads está en metrics.db, pero local_books está en library.db (vía shared SQLite o similar?)
            # En este sistema, metrics_db y library_db son archivos separados.
            # Podemos sacar los series_hash de la fuente de la DB de librería.
            pass
        return 0  # Placeholder implementation will be improved below using helper context if needed,
        # but for now I'll use a direct approach if possible.

    # --- Ratings ---

    async def add_rating(self, user_id: int, content_hash: str, rating: int):
        if self.supabase.is_active:
            try:
                data = {
                    "user_id": user_id,
                    "content_hash": content_hash,
                    "rating": rating
                }
                self.supabase.get_client().table('user_ratings').upsert(data).execute()
            except Exception as e:
                logger.error(f"Supabase metrics add_rating error: {e}")

        async with self.db_manager.connection() as conn:
            await conn.execute(
                """
                INSERT INTO user_ratings (user_id, content_hash, rating, rated_at) 
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, content_hash) DO UPDATE SET 
                    rating = excluded.rating,
                    rated_at = CURRENT_TIMESTAMP
                """,
                (user_id, content_hash, rating),
            )
            await conn.commit()

    async def get_rating_stats(self, content_hash: str) -> Dict[str, Any]:
        if not content_hash:
            return {"average": 0.0, "count": 0}
        
        if self.supabase.is_active:
            try:
                # We can't do direct AVG in wrapper easily without RPC, but we can fetch or use RPC
                # RPC is better: get_rating_stats_by_hash(p_hash text)
                # But for now, fetch all and calculate (only if not too many)
                # Ideally: rpc calls are mapped
                res = self.supabase.get_client().table('user_ratings').select("rating").eq('content_hash', content_hash).execute()
                if res.data:
                    ratings = [r['rating'] for r in res.data]
                    return {
                        "average": round(sum(ratings) / len(ratings), 1),
                        "count": len(ratings)
                    }
                return {"average": 0.0, "count": 0}
            except Exception as e:
                logger.error(f"Supabase metrics get_rating_stats error: {e}")

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT AVG(rating), COUNT(*) FROM user_ratings WHERE content_hash = ?",
                (content_hash,),
            )
            row = await cursor.fetchone()
            return {
                "average": round(row[0], 1) if row and row[0] else 0.0,
                "count": row[1] if row else 0,
            }

    async def get_series_rating_stats(self, series_hash: str) -> Dict[str, Any]:
        """Calcula el promedio y conteo de ratings de todos los libros de una serie."""
        if not series_hash:
            return {"average": 0.0, "count": 0}

        # Necesitamos unir con la tabla de libros para saber qué hashes pertenecen a la serie
        # Pero podemos simplificarlo si guardamos series_hash en user_ratings también.
        # Por ahora lo haremos vía JOIN indirecto o asumiendo que el buscador ya nos da los hashes.
        return {
            "average": 0.0,
            "count": 0,
        }  # Placeholder until series link is established


# Singleton
from core.metrics_db import metrics_db

metrics_repo = MetricsRepository(metrics_db)
