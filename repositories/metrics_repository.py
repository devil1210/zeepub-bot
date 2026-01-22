import logging
from typing import Dict, Any, Optional, List

from config.config_settings import config
from core.db_manager_pg import pg_manager
from sqlalchemy import text

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

        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    query = text("INSERT INTO user_downloads (user_id, content_hash, series_hash, title) VALUES (:user_id, :content_hash, :series_hash, :title)")
                    await session.execute(query, {"user_id": user_id, "content_hash": content_hash, "series_hash": series_hash, "title": title})
                    await session.commit()
            except Exception as e:
                logger.error(f"Postgres metrics add_download error: {e}")

    async def has_downloaded(self, user_id: int, content_hash: str) -> bool:
        if not content_hash:
            return False
        
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    query = text("SELECT 1 FROM user_downloads WHERE user_id = :user_id AND content_hash = :content_hash LIMIT 1")
                    result = await session.execute(query, {"user_id": user_id, "content_hash": content_hash})
                    if result.fetchone() is not None:
                        return True
            except Exception as e:
                logger.error(f"Postgres metrics has_downloaded error: {e}")

        # 2. Supabase Fallback (if enabled and not found locally)
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_downloads').select("id").eq('user_id', user_id).eq('content_hash', content_hash).limit(1).execute()
                if res.data: return True
            except Exception as e:
                logger.error(f"Supabase metrics has_downloaded error: {e}")

        return False

    async def get_total_downloads(self, content_hash: str) -> int:
        if not content_hash:
            return 0
        
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    query = text("SELECT COUNT(*) FROM user_downloads WHERE content_hash = :content_hash")
                    result = await session.execute(query, {"content_hash": content_hash})
                    count = result.scalar()
                    if count: return count
            except Exception as e:
                logger.error(f"Postgres metrics get_total_downloads error: {e}")

        # 2. Supabase Fallback
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('user_downloads').select("id", count='exact').eq('content_hash', content_hash).execute()
                return res.count or 0
            except Exception as e:
                logger.error(f"Supabase metrics get_total_downloads error: {e}")

        return local_count

    async def get_series_downloads(self, series_hash: str) -> int:
        if not series_hash:
            return 0
        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    query = text("SELECT COUNT(*) FROM user_downloads WHERE series_hash = :series_hash")
                    result = await session.execute(query, {"series_hash": series_hash})
                    return result.scalar() or 0
            except Exception as e:
                logger.error(f"Postgres metrics get_series_downloads error: {e}")
        return 0

    async def get_total_downloads_by_hashes(self, hashes: List[str]) -> int:
        """Calcula el total de descargas para una lista de series_hash o content_hash."""
        if not hashes:
            return 0

        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                # SQL con placeholders dinámicos para Postgres (:hash1, :hash2, etc)
                placeholders = ",".join([f":h{i}" for i in range(len(hashes))])
                query = text(f"SELECT COUNT(*) FROM user_downloads WHERE series_hash IN ({placeholders}) OR content_hash IN ({placeholders})")
                
                params = {f"h{i}": h for i, h in enumerate(hashes)}
                async with pg_manager.get_session() as session:
                    result = await session.execute(query, params)
                    return result.scalar() or 0
            except Exception as e:
                logger.error(f"Postgres metrics get_total_downloads_by_hashes error: {e}")
        return 0

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

        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    query = text("""
                        INSERT INTO user_ratings (user_id, content_hash, rating, rated_at) 
                        VALUES (:user_id, :content_hash, :rating, CURRENT_TIMESTAMP)
                        ON CONFLICT(user_id, content_hash) DO UPDATE SET 
                            rating = EXCLUDED.rating,
                            rated_at = CURRENT_TIMESTAMP
                    """)
                    await session.execute(query, {"user_id": user_id, "content_hash": content_hash, "rating": rating})
                    await session.commit()
            except Exception as e:
                logger.error(f"Postgres metrics add_rating error: {e}")

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

        if config.ENABLE_POSTGRES_PLUGIN:
            try:
                async with pg_manager.get_session() as session:
                    query = text("SELECT AVG(rating), COUNT(*) FROM user_ratings WHERE content_hash = :content_hash")
                    result = await session.execute(query, {"content_hash": content_hash})
                    row = result.fetchone()
                    return {
                        "average": round(float(row[0]), 1) if row and row[0] is not None else 0.0,
                        "count": row[1] if row else 0,
                    }
            except Exception as e:
                logger.error(f"Postgres metrics get_rating_stats error: {e}")
        return {"average": 0.0, "count": 0}

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


# Global Instance (Singleton) using pg_manager as engine
metrics_repo = MetricsRepository(None) # db_manager unused after PG migration
