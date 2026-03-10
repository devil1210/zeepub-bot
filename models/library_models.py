from typing import Optional

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String
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
    rating_average: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    book_count: Mapped[int] = mapped_column(Integer, default=0)

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
    rating_average: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    series: Mapped[Optional["Series"]] = relationship(back_populates="books")


class UserRating(TimestampedBase):
    """
    V3 Compat: User ratings for books.
    """

    __tablename__ = "user_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    book_id: Mapped[int] = mapped_column(Integer, index=True)
    book_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    rating: Mapped[int] = mapped_column(Integer)


class MetadataProposal(TimestampedBase):
    """
    V3 Compat: Metadata merges/correction proposals.
    """

    __tablename__ = "metadata_proposals"
    id: Mapped[int] = mapped_column(primary_key=True)
    series_hash: Mapped[str] = mapped_column(String(64), index=True)
    secondary_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    type: Mapped[str] = mapped_column(String(20), default="merge")  # merge, update
    proposal_data: Mapped[dict | None] = mapped_column(JSONB)


class TranslatorsGroup(TimestampedBase):
    """
    V3 Compat: Translators/Scan groups.
    """

    __tablename__ = "translators_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    siglas: Mapped[str | None] = mapped_column(String(50))


# ─────────────────────────────────────────────────────────────────────────────
# Aliases de compatibilidad V3 → V4
# ─────────────────────────────────────────────────────────────────────────────
LocalBook = Book
SeriesMetadata = Series


def __getattr__(name):
    if name == "UserDownload":
        from .user_models import DownloadLog

        return DownloadLog
    raise AttributeError(f"module {__name__} has no attribute {name}")
