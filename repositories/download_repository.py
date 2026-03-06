import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text

from core.db_manager_pg import pg_manager
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DownloadRepository(BaseRepository[dict[str, Any]]):
    """Repository for managing download history using PostgreSQL."""

    def __init__(self, db_manager=None):
        # db_manager is ignored, we use pg_manager directly
        super().__init__(None, "user_downloads")

    async def get_by_id(self, id: Any) -> dict[str, Any] | None:
        try:
            async with pg_manager.get_session() as session:
                query = text("SELECT * FROM user_downloads WHERE id = :id")
                result = await session.execute(query, {"id": id})
                row = result.fetchone()
                if not row:
                    return None
                return dict(row._mapping)
        except Exception as e:
            logger.error(f"Postgres get_by_id error: {e}")
            return None

    async def create(self, entity: dict[str, Any]) -> dict[str, Any]:
        new_id = await self.add_download(**entity)
        entity["id"] = new_id
        return entity

    async def update(self, entity: dict[str, Any]) -> dict[str, Any]:
        return entity

    async def delete(self, id: Any) -> bool:
        try:
            async with pg_manager.get_session() as session:
                await session.execute(text("DELETE FROM user_downloads WHERE id = :id"), {"id": id})
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Postgres delete error: {e}")
            return False

    async def add_download(
        self,
        user_id: int,
        title: str,
        book_hash: str,
        series_hash: str | None = None,
    ) -> int:
        try:
            async with pg_manager.get_session() as session:
                query = text("""
                    INSERT INTO user_downloads
                    (user_id, book_hash, series_hash, title, downloaded_at)
                    VALUES (:user_id, :book_hash, :series_hash, :title, CURRENT_TIMESTAMP)
                    RETURNING id
                """)
                result = await session.execute(
                    query,
                    {
                        "user_id": user_id,
                        "book_hash": book_hash,
                        "series_hash": series_hash,
                        "title": title,
                    },
                )
                new_id = result.scalar()
                await session.commit()

                # Supabase Sync (Optional, if still needed for real-time)
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

                # Trigger full bidirectional sync
                try:
                    from services.sync_service import SyncService

                    SyncService.trigger_auto_sync()
                except Exception:
                    pass

                return new_id
        except Exception as e:
            logger.error(f"Postgres add_download error: {e}")
            return 0

    async def get_user_downloads(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        try:
            async with pg_manager.get_session() as session:
                query = text("""
                    SELECT
                        dh.id,
                        dh.book_hash,
                        dh.series_hash,
                        dh.title,
                        dh.downloaded_at,
                        lb.filepath,
                        lb.volume,
                        sm.series_name,
                        sm.author
                    FROM user_downloads dh
                    JOIN local_books lb ON dh.book_hash = lb.book_hash
                    JOIN series_metadata sm ON lb.series_hash = sm.series_hash
                    WHERE dh.user_id = :user_id
                    ORDER BY dh.downloaded_at DESC
                    LIMIT :limit
                """)
                result = await session.execute(query, {"user_id": user_id, "limit": limit})
                rows = result.fetchall()
                results = []
                for row in rows:
                    item = dict(row._mapping)
                    if item.get("downloaded_at"):
                        # Ensure it's serializable
                        item["downloaded_at"] = item["downloaded_at"].isoformat()

                    # Add compatibility cover field
                    item["cover"] = item.get("cover_medium") or item.get("cover_low") or item.get("cover_original")
                    results.append(item)
                return results
        except Exception as e:
            logger.error(f"Postgres get_user_downloads error: {e}")
            return []

    async def get_download_count(self, user_id: int, since: datetime | None = None) -> int:
        try:
            async with pg_manager.get_session() as session:
                if since:
                    query = text("SELECT COUNT(*) FROM user_downloads WHERE user_id = :uid AND downloaded_at >= :since")
                    params = {"uid": user_id, "since": since}
                else:
                    query = text("SELECT COUNT(*) FROM user_downloads WHERE user_id = :uid")
                    params = {"uid": user_id}

                result = await session.execute(query, params)
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Postgres get_download_count error: {e}")
            return 0

    async def has_user_downloaded(
        self,
        user_id: int,
        title: str,
        clean_title: str | None = None,
        book_hash: str | None = None,
    ) -> bool:
        try:
            from utils.epub_extractor import clean_metadata_tags

            search_clean = clean_title or clean_metadata_tags(title)

            async with pg_manager.get_session() as session:
                if book_hash:
                    query = text("SELECT 1 FROM user_downloads WHERE user_id = :uid AND book_hash = :hash LIMIT 1")
                    if (await session.execute(query, {"uid": user_id, "hash": book_hash})).fetchone():
                        return True

                    query = text("""
                        SELECT 1 FROM user_downloads
                        WHERE user_id = :uid AND (title = :t OR clean_title = :ct OR title = :ct OR clean_title = :t)
                        LIMIT 1
                    """)
                if (await session.execute(query, {"uid": user_id, "t": title, "ct": search_clean})).fetchone():
                    return True
            return False
        except Exception as e:
            logger.error(f"Postgres has_user_downloaded error: {e}")
            return False

    async def get_total_download_count(
        self, title: str, clean_title: str | None = None, book_hash: str | None = None
    ) -> int:
        try:
            from utils.epub_extractor import clean_metadata_tags

            search_clean = clean_title or clean_metadata_tags(title)

            async with pg_manager.get_session() as session:
                if book_hash:
                    query = text("SELECT COUNT(*) FROM user_downloads WHERE book_hash = :hash")
                    count = (await session.execute(query, {"hash": book_hash})).scalar()
                    if count > 0:
                        return count

                query = text(
                    "SELECT COUNT(*) FROM user_downloads WHERE title = :t OR clean_title = :ct OR title = :ct OR clean_title = :t"
                )
                return (await session.execute(query, {"t": title, "ct": search_clean})).scalar() or 0
        except Exception as e:
            logger.error(f"Postgres get_total_download_count error: {e}")
            return 0


download_repo = DownloadRepository(None)
