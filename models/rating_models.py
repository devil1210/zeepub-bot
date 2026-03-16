from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class UserRating(Base):
    """
    V4 User Rating Entity.
    """

    __tablename__ = "user_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), index=True, nullable=False)
    book_id = Column(BigInteger, ForeignKey("books.id"), index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    book_hash = Column(String(64), index=True)

    user = relationship("User", backref="ratings")
    book = relationship("Book", backref="ratings")
