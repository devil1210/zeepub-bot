import logging
from typing import Any

from sqlalchemy import delete, func, select

from core.db_manager_pg import pg_manager
from models.library import LocalBook, UserRating

logger = logging.getLogger(__name__)


class RatingService:
    @staticmethod
    async def rate_book(user_id: int, book_hash: str, rating: int) -> dict[str, Any]:
        """
        Registra el voto de un usuario y actualiza el promedio del libro (Async).
        Retorna el nuevo promedio y total de votos.
        """
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        async with pg_manager.get_session() as session:
            try:
                # 1. Fetch book if not found (needed for book_hash)
                book_stmt = select(LocalBook).where(LocalBook.book_hash == book_hash)
                book_res = await session.execute(book_stmt)
                book = book_res.scalar_one_or_none()

                if not book:
                    raise ValueError(f"Book with hash {book_hash} not found")

                # 2. Upsert rating
                stmt = select(UserRating).filter_by(user_id=user_id, book_hash=book_hash)
                res = await session.execute(stmt)
                existing = res.scalar_one_or_none()

                if existing:
                    existing.rating = rating
                    existing.book_hash = book.book_hash
                else:
                    new_rating = UserRating(
                        user_id=user_id,
                        book_hash=book_hash,
                        rating=rating,
                    )
                    session.add(new_rating)

                await session.flush()  # Ensure rating is applied for subsequent stats

                # 3. Recalculate Book Average
                stats_stmt = select(func.avg(UserRating.rating), func.count(UserRating.rating)).where(
                    UserRating.book_hash == book_hash
                )

                stats_res = await session.execute(stats_stmt)
                stats = stats_res.fetchone()

                new_avg = round(float(stats[0]), 2) if stats[0] else 0.0
                new_count = stats[1] if stats[1] else 0

                # 4. Update LocalBook Cache columns
                if book:
                    book.rating_average = new_avg
                    book.rating_count = new_count

                await session.commit()

                # Trigger sync to Cloud
                from services.sync_service import SyncService

                SyncService.trigger_auto_sync()

                return {
                    "book_hash": book_hash,
                    "new_average": new_avg,
                    "total_votes": new_count,
                    "user_rating": rating,
                }

            except Exception as e:
                logger.error(f"Error rating book {book_hash}: {e}")
                raise

    @staticmethod
    async def remove_rating(user_id: int, book_hash: str) -> dict[str, Any]:
        """
        Elimina el voto de un usuario y recalcula el promedio (Async).
        """
        async with pg_manager.get_session() as session:
            try:
                # 1. Delete rating
                stmt = delete(UserRating).where(UserRating.user_id == user_id, UserRating.book_hash == book_hash)
                await session.execute(stmt)
                await session.flush()

                # 2. Recalculate Book Average
                stats_stmt = select(func.avg(UserRating.rating), func.count(UserRating.rating)).where(
                    UserRating.book_hash == book_hash
                )

                stats_res = await session.execute(stats_stmt)
                stats = stats_res.fetchone()

                new_avg = round(float(stats[0]), 2) if stats[0] else 0.0
                new_count = stats[1] if stats[1] else 0

                # 3. Update LocalBook
                book_stmt = select(LocalBook).where(LocalBook.book_hash == book_hash)
                book_res = await session.execute(book_stmt)
                book = book_res.scalar_one_or_none()

                if book:
                    book.rating_average = new_avg
                    book.rating_count = new_count

                await session.commit()

                # Trigger sync to Cloud
                from services.sync_service import SyncService

                SyncService.trigger_auto_sync()

                return {
                    "success": True,
                    "book_hash": book_hash,
                    "new_average": new_avg,
                    "total_votes": new_count,
                    "user_rating": None,
                }
            except Exception as e:
                logger.error(f"Error removing rating for book {book_hash}: {e}")
                raise

    @staticmethod
    async def get_user_rating(user_id: int, book_hash: str) -> int | None:
        """Retorna el voto previo del usuario si existe (Async)."""
        async with pg_manager.get_session() as session:
            try:
                stmt = select(UserRating.rating).where(UserRating.user_id == user_id, UserRating.book_hash == book_hash)
                res = await session.execute(stmt)
                return res.scalar_one_or_none()
            except Exception as e:
                logger.error(f"Error fetching user rating: {e}")
                return None

    @staticmethod
    async def get_rating_breakdown(book_hash: str) -> dict[int, int]:
        """
        Retorna el desglose de votos por estrella (Async).
        Returns: {1: count, 2: count, 3: count, 4: count, 5: count}
        """
        async with pg_manager.get_session() as session:
            try:
                breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

                stmt = (
                    select(UserRating.rating, func.count(UserRating.id))
                    .where(UserRating.book_hash == book_hash)
                    .group_by(UserRating.rating)
                )

                res = await session.execute(stmt)
                results = res.fetchall()

                for rating, count in results:
                    if 1 <= rating <= 5:
                        breakdown[rating] = count

                return breakdown
            except Exception as e:
                logger.error(f"Error fetching rating breakdown for {book_hash}: {e}")
                return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
