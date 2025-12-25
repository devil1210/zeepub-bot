import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DownloadRepository(BaseRepository[Dict[str, Any]]):
    """Repository for managing download history."""

    def __init__(self, db_manager):
        super().__init__(db_manager, "download_history")

    async def add_download(
        self,
        user_id: int,
        title: str,
        author: Optional[str] = None,
        download_url: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> int:
        """
        Record a download in the history.

        Args:
            user_id: Telegram user ID
            title: Book title
            author: Book author (optional)
            download_url: URL of the downloaded file (optional)
            file_size: File size in bytes (optional)

        Returns:
            ID of the created record
        """
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO download_history 
                (user_id, title, author, download_url, file_size)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, title, author, download_url, file_size)
            )
            await conn.commit()
            return cursor.lastrowid

    async def get_user_downloads(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent downloads for a specific user.

        Args:
            user_id: Telegram user ID
            limit: Maximum number of downloads to return

        Returns:
            List of download records
        """
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                """
                SELECT id, title, author, file_size, downloaded_at
                FROM download_history
                WHERE user_id = ?
                ORDER BY downloaded_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
            rows = await cursor.fetchall()

            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "author": row[2] or "Desconocido",
                    "file_size": row[3],
                    "downloaded_at": row[4]
                }
                for row in rows
            ]

    async def get_download_count(
        self,
        user_id: int,
        since: Optional[datetime] = None
    ) -> int:
        """
        Count downloads for a user, optionally since a specific date.

        Args:
            user_id: Telegram user ID
            since: Optional datetime to count from

        Returns:
            Number of downloads
        """
        async with self.db_manager.connection() as conn:
            if since:
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM download_history
                    WHERE user_id = ? AND downloaded_at >= ?
                    """,
                    (user_id, since.isoformat())
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*)
                    FROM download_history
                    WHERE user_id = ?
                    """,
                    (user_id,)
                )

            row = await cursor.fetchone()
            return row[0] if row else 0


# Global instance
from core.db_manager import db_manager
download_repo = DownloadRepository(db_manager)
