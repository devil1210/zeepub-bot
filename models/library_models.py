import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase

if TYPE_CHECKING:
    pass


class LibrarySource(TimestampedBase):
    """
    V4 Library Source Entity.
    Represents a root folder or source of book files.
    """

    __tablename__ = "library_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    last_scanned: Mapped[any] = mapped_column(DateTime(timezone=True), nullable=True)

    series: Mapped[list["Series"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class Series(TimestampedBase):
    """
    V4 Series Entity.
    Identified primarily by its hash and source.
    """

    __tablename__ = "series"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("library_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Core metadata
    title_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    title_spanish: Mapped[str | None] = mapped_column(String(512))

    # UI Metadata
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))

    # Identification/Status
    slug: Mapped[str | None] = mapped_column(String(100), index=True)  # For Telegram hashtags
    status: Mapped[str] = mapped_column(String(20), default="reading")  # 'reading', 'completed', 'dropped'
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))  # Gemini embeddings

    # Relationships
    source: Mapped["LibrarySource"] = relationship(back_populates="series")
    books: Mapped[list["Book"]] = relationship(back_populates="series", cascade="all, delete-orphan")

    # Compatibility Aliases (V3 legacy support)
    @hybrid_property
    def series_name(self) -> str:
        return self.title_raw

    @series_name.setter
    def series_name(self, value: str):
        self.title_raw = value

    @hybrid_property
    def series_hash(self) -> str:
        return self.hash

    @series_hash.setter
    def series_hash(self, value: str):
        self.hash = value


class Book(TimestampedBase):
    """
    V4 Book Entity.
    Identity and global uniqueness are managed via UUID and hash.
    """

    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # File Metadata
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(BigInteger)
    extension: Mapped[str] = mapped_column(String(10))

    # Content Metadata
    volume_number: Mapped[float] = mapped_column(Numeric, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Status
    detected_at: Mapped[any] = mapped_column(DateTime(timezone=True), server_default="now()")
    is_published: Mapped[bool] = mapped_column(default=False)

    # Relationships
    series: Mapped["Series"] = relationship(back_populates="books")

    # Compatibility Aliases (V3 legacy support)
    @hybrid_property
    def filepath(self) -> str:
        return self.file_path

    @filepath.setter
    def filepath(self, value: str):
        self.file_path = value

    @hybrid_property
    def volume(self) -> float:
        return self.volume_number

    @volume.setter
    def volume(self, value: float):
        self.volume_number = value

    @hybrid_property
    def book_hash(self) -> str:
        return self.hash

    @book_hash.setter
    def book_hash(self, value: str):
        self.hash = value

    @hybrid_property
    def series_hash(self) -> str | None:
        return self.series.hash if self.series else None

    @hybrid_property
    def source_id(self) -> uuid.UUID | None:
        return self.series.source_id if self.series else None


# Mapping legacy class names
LocalBook = Book
SeriesMetadata = Series


class MetadataProposal(TimestampedBase):
    """
    V4 Metadata Proposal Entity.
    Stores AI-generated suggestions for series/book metadata.
    """

    __tablename__ = "metadata_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Proposed Changes
    proposed_title_spanish: Mapped[str | None] = mapped_column(String(512))
    proposed_description: Mapped[str | None] = mapped_column(Text)
    proposed_slug: Mapped[str | None] = mapped_column(String(100))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'applied', 'rejected'
    ai_confidence: Mapped[float | None] = mapped_column(Numeric)

    # Metadata context
    raw_response: Mapped[dict | None] = mapped_column(JSONB, default=dict)
