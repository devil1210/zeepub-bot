from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase


class Series(TimestampedBase):
    """
    V4 Series Entity.
    Represents a collection of books (e.g., a Manga or Light Novel series).
    """

    __tablename__ = "series"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Core Identity
    series_name: Mapped[str] = mapped_column(String(255), nullable=False)
    series_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    slug: Mapped[str | None] = mapped_column(String(512), index=True)

    # AI/Localization Enriched Data
    series_spanish: Mapped[str | None] = mapped_column(String(255))
    series_english: Mapped[str | None] = mapped_column(String(255))

    # People
    author: Mapped[str | None] = mapped_column(String(255))
    illustrator: Mapped[str | None] = mapped_column(String(255))

    # Rich Metadata
    description: Mapped[str | None] = mapped_column(String(5000))
    tags: Mapped[list | None] = mapped_column(JSONB)
    demographics: Mapped[list | None] = mapped_column(JSONB)

    # Visuals & Stats
    cover_url: Mapped[str | None] = mapped_column(String(1024))
    book_type: Mapped[str | None] = mapped_column(String(100))
    publisher: Mapped[str | None] = mapped_column(String(255))
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    books: Mapped[list["Book"]] = relationship(back_populates="series", cascade="all, delete-orphan")


class Book(TimestampedBase):
    """
    V4 Book Entity.
    The physical/digital representation of a volume or chapter.
    """

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The absolute truth of a book identity
    book_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    # File traceability
    filepath: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)

    # Extracted Info
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    volume: Mapped[float | None] = mapped_column(Float)
    language: Mapped[str] = mapped_column(String(10), default="es")

    # UI progressive covers
    cover_low: Mapped[str | None] = mapped_column(String(1024))
    cover_medium: Mapped[str | None] = mapped_column(String(1024))
    cover_high: Mapped[str | None] = mapped_column(String(1024))
    cover_original: Mapped[str | None] = mapped_column(String(1024))

    # Foreign Keys
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id"), index=True)

    # Relationships
    series: Mapped[Optional["Series"]] = relationship(back_populates="books")
