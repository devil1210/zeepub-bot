import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DownloadRepository(BaseRepository[Dict[str, Any]]):
    """Repository for managing download history."""

    def __init__(self, db_manager):
        super().__init__(db_manager, "download_history")

    # --- Abstract Methods Implementation ---

    async def get_by_id(self, id: Any) -> Optional[Dict[str, Any]]:
        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM download_history WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            # Assuming row factory or manual mapping. For now manual.
            # Using cursor.description could be better but let's stick to basic
            cols = [description[0] for description in cursor.description]
            return dict(zip(cols, row))

    async def create(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a download record from a dictionary entity."""
        # This wraps add_download logic
        new_id = await self.add_download(
            user_id=entity["user_id"],
            title=entity["title"],
            author=entity.get("author"),
            download_url=entity.get("download_url"),
            file_size=entity.get("file_size")
        )
        entity["id"] = new_id
        return entity

    async def update(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Updates not usually supported for history logs, but implementing for interface."""
        # Minimal implementation
        return entity

    async def delete(self, id: Any) -> bool:
        """Deletes a download record."""
        async with self.db_manager.connection() as conn:
            await conn.execute("DELETE FROM download_history WHERE id = ?", (id,))
            await conn.commit()
            return True

    # --- Specific Methods ---

    async def add_download(
        self,
        user_id: int,
        title: str,
        author: Optional[str] = None,
        download_url: Optional[str] = None,
        file_size: Optional[int] = None,
        romaji_title: Optional[str] = None,
        series: Optional[str] = None,
        volume: Optional[str] = None,
        translator: Optional[str] = None,
        clean_title: Optional[str] = None
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
                (user_id, title, author, download_url, file_size, romaji_title, series, volume, translator, clean_title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, author, download_url, file_size, romaji_title, series, volume, translator, clean_title)
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
                SELECT id, title, author, file_size, downloaded_at, romaji_title, series, volume, translator, clean_title
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
                    "downloaded_at": row[4],
                    "romaji_title": row[5],
                    "series": row[6],
                    "volume": row[7],
                    "translator": row[8],
                    "clean_title": row[9]
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

    async def has_user_downloaded(self, user_id: int, title: str, clean_title: Optional[str] = None) -> bool:
        """
        Check if a user has previously downloaded a book by title or clean_title.
        """
        from utils.epub_extractor import clean_metadata_tags

        search_clean = clean_title or clean_metadata_tags(title)

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                """
                SELECT 1 FROM download_history 
                WHERE user_id = ? AND (title = ? OR clean_title = ? OR title = ?)
                """,
                (user_id, title, search_clean, search_clean)
            )
            return await cursor.fetchone() is not None

    async def get_total_download_count(self, title: str, clean_title: Optional[str] = None) -> int:
        """
        Get total download count for a book across all users, using both dirty and clean titles.
        """
        from utils.epub_extractor import clean_metadata_tags

        search_clean = clean_title or clean_metadata_tags(title)

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                """
                SELECT COUNT(*) FROM download_history 
                WHERE title = ? OR clean_title = ? OR title = ?
                """,
                (title, search_clean, search_clean)
            )
            row = await cursor.fetchone()
            return row[0] if row else 0


# Global instance
from core.db_manager import db_manager
download_repo = DownloadRepository(db_manager)
