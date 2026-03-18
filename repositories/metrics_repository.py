import logging
from typing import Any

from sqlalchemy import text

from core.db_manager_pg import pg_manager

logger = logging.getLogger(__name__)


class MetricsRepository:
    """Repositorio centralizado para descargas y valoraciones basadas en PostgreSQL."""

    def __init__(self, session=None, db_manager=None):
        from core.supabase_manager import supabase_manager

        self.injected_session = session
        self.db_manager = db_manager or pg_manager
        self.supabase = supabase_manager

    async def _get_session(self):
        if self.injected_session:
            yield self.injected_session
        else:
            async with self._get_session() as session:
                yield session

    async def add_download(
        self,
        user_id: int,
        book_hash: str,
        series_hash: str | None = None,
        title: str | None = None,
    ):
        try:
            async with self._get_session() as session:
                query = text(
                    "INSERT INTO user_downloads (user_id, book_hash, series_hash, title, downloaded_at) VALUES (:user_id, :book_hash, :series_hash, :title, CURRENT_TIMESTAMP)"
                )
                await session.execute(
                    query,
                    {
                        "user_id": user_id,
                        "book_hash": book_hash,
                        "series_hash": series_hash,
                        "title": title,
                    },
                )
                if self.injected_session is None:
                    await session.commit()

            if self.supabase.is_active:
                try:
                    data = {
                        "user_id": user_id,
                        "book_hash": book_hash,
                        "series_hash": series_hash,
                        "title": title,
                    }
                    self.supabase.get_client().table("user_downloads").insert(data).execute()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Postgres metrics add_download error: {e}")

    async def has_downloaded(self, user_id: int, book_hash: str) -> bool:
        if not book_hash:
            return False
        try:
            async with self._get_session() as session:
                query = text("SELECT 1 FROM user_downloads WHERE user_id = :user_id AND book_hash = :book_hash LIMIT 1")
                result = await session.execute(query, {"user_id": user_id, "book_hash": book_hash})
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Postgres metrics has_downloaded error: {e}")
        return False

    async def get_total_downloads(self, book_hash: str) -> int:
        if not book_hash:
            return 0
        try:
            async with self._get_session() as session:
                query = text("SELECT COUNT(*) FROM user_downloads WHERE book_hash = :book_hash")
                result = await session.execute(query, {"book_hash": book_hash})
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Postgres metrics get_total_downloads error: {e}")
            return 0

    async def get_series_downloads(self, series_hash: str) -> int:
        if not series_hash:
            return 0
        try:
            async with self._get_session() as session:
                query = text("SELECT COUNT(*) FROM user_downloads WHERE series_hash = :series_hash")
                result = await session.execute(query, {"series_hash": series_hash})
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Postgres metrics get_series_downloads error: {e}")
            return 0

    async def get_total_downloads_by_hashes(self, hashes: list[str]) -> int:
        if not hashes:
            return 0
        try:
            placeholders = ",".join([f":h{i}" for i in range(len(hashes))])
            query = text(
                f"SELECT COUNT(*) FROM user_downloads WHERE series_hash IN ({placeholders}) OR book_hash IN ({placeholders})"
            )
            params = {f"h{i}": h for i, h in enumerate(hashes)}
            async with self._get_session() as session:
                result = await session.execute(query, params)
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Postgres metrics get_total_downloads_by_hashes error: {e}")
            return 0

    async def add_rating(self, user_id: int, book_hash: str, rating: int):
        try:
            async with self._get_session() as session:
                query = text("""
                    INSERT INTO user_ratings (user_id, book_hash, rating, rated_at)
                    VALUES (:user_id, :book_hash, :rating, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id, book_hash) DO UPDATE SET
                        rating = EXCLUDED.rating,
                        rated_at = CURRENT_TIMESTAMP
                """)
                await session.execute(
                    query,
                    {"user_id": user_id, "book_hash": book_hash, "rating": rating},
                )
                if self.injected_session is None:
                    await session.commit()

            if self.supabase.is_active:
                try:
                    data = {
                        "user_id": user_id,
                        "book_hash": book_hash,
                        "rating": rating,
                    }
                    self.supabase.get_client().table("user_ratings").upsert(data).execute()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Postgres metrics add_rating error: {e}")

    async def get_rating_stats(self, book_hash: str) -> dict[str, Any]:
        if not book_hash:
            return {"average": 0.0, "count": 0}
        try:
            async with self._get_session() as session:
                query = text("SELECT AVG(rating), COUNT(*) FROM user_ratings WHERE book_hash = :book_hash")
                result = await session.execute(query, {"book_hash": book_hash})
                row = result.fetchone()
                return {
                    "average": round(float(row[0]), 1) if row and row[0] is not None else 0.0,
                    "count": row[1] if row else 0,
                }
        except Exception as e:
            logger.error(f"Postgres metrics get_rating_stats error: {e}")
            return {"average": 0.0, "count": 0}


metrics_repo = MetricsRepository(None)
