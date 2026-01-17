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
        clean_title: Optional[str] = None,
        book_hash: Optional[str] = None
    ) -> int:
        if self.supabase.is_active:
            try:
                data = {
                    "user_id": user_id,
                    "title": title,
                    "author": author,
                    "download_url": download_url,
                    "file_size": file_size,
                    "romaji_title": romaji_title,
                    "series": series,
                    "volume": volume,
                    "translator": translator,
                    "clean_title": clean_title,
                    "book_hash": book_hash
                }
                res = self.supabase.get_client().table('download_history').insert(data).execute()
                if res.data:
                    return res.data[0]['id']
            except Exception as e:
                logger.error(f"Supabase add_download error: {e}")

        async with self.db_manager.connection() as conn:
            cursor = await conn.execute(
                """
                INSERT INTO download_history
                (user_id, title, author, download_url, file_size, romaji_title, series, volume, translator, clean_title, book_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, title, author, download_url, file_size, romaji_title, series, volume, translator, clean_title, book_hash)
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
        """
        # 1. Try Local First
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
            
            if rows:
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

        # 2. Supabase Fallback
        if self.supabase.is_active:
            try:
                res = self.supabase.get_client().table('download_history').select("*").eq('user_id', user_id).order('downloaded_at', desc=True).limit(limit).execute()
                if res.data:
                    return [
                        {
                            "id": row['id'],
                            "title": row['title'],
                            "author": row['author'] or "Desconocido",
                            "file_size": row['file_size'],
                            "downloaded_at": row['downloaded_at'],
                            "romaji_title": row['romaji_title'],
                            "series": row['series'],
                            "volume": row['volume'],
                            "translator": row['translator'],
                            "clean_title": row['clean_title']
                        }
                        for row in res.data
                    ]
            except Exception as e:
                logger.error(f"Supabase get_user_downloads error: {e}")

        return []

    async def get_download_count(
        self,
        user_id: int,
        since: Optional[datetime] = None
    ) -> int:
        """
        Count downloads for a user, optionally since a specific date.
        """
        # 1. Try Local First
        local_count = 0
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
            local_count = row[0] if row else 0
        
        if local_count > 0:
            return local_count

        # 2. Supabase Fallback
        if self.supabase.is_active:
            try:
                query = self.supabase.get_client().table('download_history').select("id", count='exact').eq('user_id', user_id)
                if since:
                    query = query.gte('downloaded_at', since.isoformat())
                res = query.execute()
                return res.count or 0
            except Exception as e:
                logger.error(f"Supabase get_download_count error: {e}")

        return local_count

    async def has_user_downloaded(self, user_id: int, title: str, clean_title: Optional[str] = None, book_hash: Optional[str] = None) -> bool:
        """
        Check if a user has previously downloaded a book.
        """
        # 1. Try Local First
        async with self.db_manager.connection() as conn:
            # Check Hash
            if book_hash:
                cursor = await conn.execute(
                    "SELECT 1 FROM download_history WHERE user_id = ? AND book_hash = ?",
                    (user_id, book_hash)
                )
                if await cursor.fetchone():
                    return True

            # Check Titles
            from utils.epub_extractor import clean_metadata_tags
            search_clean = clean_title or clean_metadata_tags(title)

            cursor = await conn.execute(
                """
                SELECT 1 FROM download_history 
                WHERE user_id = ? AND (
                    title = ? OR 
                    clean_title = ? OR 
                    title = ? OR 
                    clean_title = ?
                )
                """,
                (user_id, title, search_clean, search_clean, title)
            )
            if await cursor.fetchone():
                return True

        # 2. Supabase Fallback
        if self.supabase.is_active:
            try:
                # 1. Check Hash
                if book_hash:
                    res = self.supabase.get_client().table('download_history').select("id").eq('user_id', user_id).eq('book_hash', book_hash).limit(1).execute()
                    if res.data: return True
                
                # 2. Check Titles
                from utils.epub_extractor import clean_metadata_tags
                search_clean = clean_title or clean_metadata_tags(title)
                res = self.supabase.get_client().table('download_history').select("id").eq('user_id', user_id).or_(f"title.eq.{title},clean_title.eq.{search_clean},title.eq.{search_clean},clean_title.eq.{title}").limit(1).execute()
                if res.data: return True
            except Exception as e:
                logger.error(f"Supabase has_user_downloaded error: {e}")

        return False

    async def get_total_download_count(self, title: str, clean_title: Optional[str] = None, book_hash: Optional[str] = None) -> int:
        """
        Get total download count for a book across all users.
        """
        # 1. Try Local First
        local_count = 0
        async with self.db_manager.connection() as conn:
            # Check Hash
            if book_hash:
                cursor = await conn.execute(
                    "SELECT COUNT(*) FROM download_history WHERE book_hash = ?",
                    (book_hash,)
                )
                local_count = (await cursor.fetchone())[0]
            
            # Check Title if hash didn't work or not provided
            if local_count == 0:
                from utils.epub_extractor import clean_metadata_tags
                search_clean = clean_title or clean_metadata_tags(title)

                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) FROM download_history 
                    WHERE title = ? OR clean_title = ? OR title = ? OR clean_title = ?
                    """,
                    (title, search_clean, search_clean, title)
                )
                row = await cursor.fetchone()
                local_count = row[0] if row else 0

        if local_count > 0:
            return local_count

        # 2. Supabase Fallback
        if self.supabase.is_active:
            try:
                if book_hash:
                    res = self.supabase.get_client().table('download_history').select("id", count='exact').eq('book_hash', book_hash).execute()
                    if res.count > 0: return res.count
                
                from utils.epub_extractor import clean_metadata_tags
                search_clean = clean_title or clean_metadata_tags(title)
                res = self.supabase.get_client().table('download_history').select("id", count='exact').or_(f"title.eq.{title},clean_title.eq.{search_clean}").execute()
                return res.count or 0
            except Exception as e:
                logger.error(f"Supabase get_total_download_count error: {e}")

        return local_count


# Global instance
from core.db_manager import db_manager
download_repo = DownloadRepository(db_manager)
