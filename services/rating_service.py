import logging
from typing import Dict, Any, Optional
from sqlalchemy import func
from core.db_manager import db_manager
from utils.library_db import get_session
from models.library_models import UserRating, LocalBook

logger = logging.getLogger(__name__)


class RatingService:
    @staticmethod
    def rate_book(user_id: int, book_id: int, rating: int) -> Dict[str, Any]:
        """
        Registra el voto de un usuario y actualiza el promedio del libro.
        Retorna el nuevo promedio y total de votos.
        """
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")
            
        session = get_session()
        try:
            # 1. Upsert rating (Insert or Replace)
            # Check existance first
            existing = session.query(UserRating).filter_by(user_id=user_id, book_id=book_id).first()
            
            if existing:
                existing.rating = rating
            else:
                new_rating = UserRating(user_id=user_id, book_id=book_id, rating=rating)
                session.add(new_rating)
            
            session.commit()
            
            # 2. Recalculate Book Average
            # Este query hace el cálculo agregado eficiente
            stats = session.query(
                func.avg(UserRating.rating),
                func.count(UserRating.rating)
            ).filter_by(book_id=book_id).first()
            
            new_avg = round(stats[0], 2) if stats[0] else 0.0
            new_count = stats[1] if stats[1] else 0
            
            # 3. Update LocalBook Cache columns
            book = session.query(LocalBook).filter_by(id=book_id).first()
            if book:
                book.rating_average = new_avg
                book.rating_count = new_count
                session.commit()
                
            return {
                "book_id": book_id,
                "new_average": new_avg,
                "total_votes": new_count,
                "user_rating": rating
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error rating book {book_id}: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def remove_rating(user_id: int, book_id: int) -> Dict[str, Any]:
        """
        Elimina el voto de un usuario y recalcula el promedio.
        """
        session = get_session()
        try:
            # 1. Delete rating
            existing = session.query(UserRating).filter_by(user_id=user_id, book_id=book_id).first()
            if existing:
                session.delete(existing)
                session.commit()
            
            # 2. Recalculate Book Average
            stats = session.query(
                func.avg(UserRating.rating),
                func.count(UserRating.rating)
            ).filter_by(book_id=book_id).first()
            
            new_avg = round(stats[0], 2) if stats[0] else 0.0
            new_count = stats[1] if stats[1] else 0
            
            # 3. Update LocalBook
            book = session.query(LocalBook).filter_by(id=book_id).first()
            if book:
                book.rating_average = new_avg
                book.rating_count = new_count
                session.commit()
                
            return {
                "success": True,
                "book_id": book_id,
                "new_average": new_avg,
                "total_votes": new_count,
                "user_rating": None
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error removing rating for book {book_id}: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def get_user_rating(user_id: int, book_id: int) -> Optional[int]:
        """Retorna el voto previo del usuario si existe."""
        session = get_session()
        try:
            rating = session.query(UserRating).filter_by(user_id=user_id, book_id=book_id).first()
            return rating.rating if rating else None
        finally:
            session.close()

    @staticmethod
    def get_rating_breakdown(book_id: int) -> Dict[int, int]:
        """
        Retorna el desglose de votos por estrella.
        Returns: {1: count, 2: count, 3: count, 4: count, 5: count}
        """
        session = get_session()
        try:
            # Get count for each rating value
            breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            results = session.query(
                UserRating.rating,
                func.count(UserRating.id)
            ).filter_by(book_id=book_id).group_by(UserRating.rating).all()
            
            for rating, count in results:
                if 1 <= rating <= 5:
                    breakdown[rating] = count
                    
            return breakdown
        finally:
            session.close()
