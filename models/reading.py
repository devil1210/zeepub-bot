import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class KoreaderBookHash(Base):
    """
    Mapeo bidireccional entre el hash partial MD5 de KOReader (32 hex)
    y el identificador único del libro en ZeePub-bot (UUIDv7 / SHA-256).
    """

    __tablename__ = "koreader_book_hashes"

    koreader_hash: Mapped[str] = mapped_column(String(32), primary_key=True, index=True)
    book_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    book = relationship("Book", foreign_keys=[book_id], backref="koreader_hashes")


class ReadingProgress(Base):
    """
    Progreso de lectura sincronizado por usuario y libro.
    Compatible con Web Reader (Foliate-js), KOReader (kosync) y e-readers físicos.
    """

    __tablename__ = "reading_progress"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    book_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    progress_cfi: Mapped[str | None] = mapped_column(String(512), nullable=True)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book_reading_progress"),
        Index("idx_reading_progress_user_book", "user_id", "book_id"),
    )

    book = relationship("Book", foreign_keys=[book_id], backref="reading_progresses")
