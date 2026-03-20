import uuid
from datetime import datetime

# from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.rating_models import UserRating  # noqa: F401
from models.translators_models import TranslatorsGroup  # noqa: F401
from models.user_models import DownloadLog as UserDownload  # noqa: F401

from .base import TimestampedBase


class LibrarySource(TimestampedBase):
    __tablename__ = "library_sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    last_scanned: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    series: Mapped[list["Series"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class Series(TimestampedBase):
    __tablename__ = "series"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("library_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    title_spanish: Mapped[str | None] = mapped_column(String(512))
    title_english: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    author: Mapped[str | None] = mapped_column(String(512))
    author_jap: Mapped[str | None] = mapped_column(String(512))
    illustrator: Mapped[str | None] = mapped_column(String(512))
    illustrator_jap: Mapped[str | None] = mapped_column(String(512))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    rating_average: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)
    rating_count: Mapped[int] = mapped_column(default=0)
    book_count: Mapped[int] = mapped_column(default=0)
    book_type: Mapped[str | None] = mapped_column(String(50))
    publisher: Mapped[str | None] = mapped_column(String(255))
    demographics: Mapped[dict | None] = mapped_column(JSON, default=dict)
    slug: Mapped[str | None] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="reading")
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    source: Mapped["LibrarySource"] = relationship(back_populates="series")
    books: Mapped[list["Book"]] = relationship(back_populates="series", cascade="all, delete-orphan")

    @hybrid_property
    def series_spanish(self) -> str | None:
        return self.title_spanish

    @series_spanish.setter
    def series_spanish(self, value: str | None):
        self.title_spanish = value

    @hybrid_property
    def series_english(self) -> str | None:
        return self.title_english

    @series_english.setter
    def series_english(self, value: str | None):
        self.title_english = value

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
    __tablename__ = "books"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id_col: Mapped[uuid.UUID | None] = mapped_column(
        "source_id", ForeignKey("library_sources.id", ondelete="CASCADE"), nullable=True, index=True
    )
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(BigInteger)
    extension: Mapped[str] = mapped_column(String(10))
    volume_number: Mapped[float] = mapped_column(Numeric, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    # V4 Library Extension
    filename: Mapped[str | None] = mapped_column(String(512))
    file_modified_at: Mapped[float | None] = mapped_column(Numeric)
    file_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[str | None] = mapped_column(String(10), default="es")
    translator: Mapped[str | None] = mapped_column(String(255))
    layout_by: Mapped[str | None] = mapped_column(String(255))
    author_col: Mapped[str | None] = mapped_column("author", String(512))
    author_jap: Mapped[str | None] = mapped_column(String(512))
    illustrator: Mapped[str | None] = mapped_column(String(512))
    illustrator_jap: Mapped[str | None] = mapped_column(String(512))
    english_title: Mapped[str | None] = mapped_column(String(512))
    jap_title: Mapped[str | None] = mapped_column(String(512))
    romaji_title: Mapped[str | None] = mapped_column(String(512))
    book_type_col: Mapped[str | None] = mapped_column("book_type", String(50))
    edition: Mapped[str | None] = mapped_column(String(100))
    publisher: Mapped[str | None] = mapped_column(String(255))
    extracted_data: Mapped[dict | None] = mapped_column(JSON, default=dict)
    hash_md5: Mapped[str | None] = mapped_column(String(64))
    isbn: Mapped[str | None] = mapped_column(String(50))
    asin: Mapped[str | None] = mapped_column(String(50))
    uri_id: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[str | None] = mapped_column(String(100))
    modified_at_opf: Mapped[str | None] = mapped_column(String(100))
    epub_version: Mapped[str | None] = mapped_column(String(20))
    word_count: Mapped[int | None] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    reading_time: Mapped[int | None] = mapped_column(Integer)
    is_uncensored: Mapped[bool] = mapped_column(default=False)
    color_mode: Mapped[str | None] = mapped_column(String(20), default="bw")
    series_hash_col: Mapped[str | None] = mapped_column("series_hash", String(64))
    short_link: Mapped[str | None] = mapped_column(String(100))
    cover_original: Mapped[str | None] = mapped_column(String(512))
    cover_high: Mapped[str | None] = mapped_column(String(512))
    cover_medium: Mapped[str | None] = mapped_column(String(512))
    cover_low: Mapped[str | None] = mapped_column(String(512))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    rating_count: Mapped[int | None] = mapped_column(Integer, default=0)
    rating_average: Mapped[float | None] = mapped_column(Numeric, default=0.0)

    # Relationships
    series: Mapped["Series"] = relationship(back_populates="books")

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
        self.volume_number = float(value) if value is not None else 0.0

    @hybrid_property
    def book_hash(self) -> str:
        return self.hash

    @book_hash.setter
    def book_hash(self, value: str):
        self.hash = value

    @hybrid_property
    def series_hash(self) -> str | None:
        return self.series_hash_col or (self.series.hash if self.series else None)

    @series_hash.setter
    def series_hash(self, value: str):
        self.series_hash_col = value

    @hybrid_property
    def author(self) -> str:
        return self.author_col or (self.series.author if self.series else "Unknown")

    @author.setter
    def author(self, value: str):
        self.author_col = value

    @hybrid_property
    def book_type(self) -> str:
        return self.book_type_col or (self.series.book_type if self.series else "Light Novel")

    @book_type.setter
    def book_type(self, value: str):
        self.book_type_col = value

    @hybrid_property
    def source_id(self) -> uuid.UUID | None:
        return self.source_id_col or (self.series.source_id if self.series else None)

    @source_id.setter
    def source_id(self, value: uuid.UUID | None):
        self.source_id_col = value


# Mapping legacy class names
LocalBook = Book
SeriesMetadata = Series


class ArchivedSeries(TimestampedBase):
    __tablename__ = "archived_series"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title_raw: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(512))
    title_spanish: Mapped[str | None] = mapped_column(String(512))
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    book_type: Mapped[str | None] = mapped_column(String(50))
    publisher: Mapped[str | None] = mapped_column(String(255))
    original_series_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class ArchivedBook(TimestampedBase):
    __tablename__ = "archived_books"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_hash: Mapped[str] = mapped_column(String(64), index=True)
    book_hash: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    filename: Mapped[str | None] = mapped_column(String(512))
    last_filepath: Mapped[str | None] = mapped_column(Text)
    volume: Mapped[float | None] = mapped_column(Numeric)
    author: Mapped[str | None] = mapped_column(String(255))
    book_type: Mapped[str | None] = mapped_column(String(50))
    original_book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str | None] = mapped_column(String(100))
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class UploadBook(TimestampedBase):
    __tablename__ = "upload_books"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processed, failed
    metadata_json: Mapped[dict | None] = mapped_column(JSON, default=dict)


class DuplicateBook(TimestampedBase):
    __tablename__ = "duplicate_books"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_hash: Mapped[str] = mapped_column(String(64), index=True)
    original_filepath: Mapped[str] = mapped_column(Text)
    duplicate_filepath: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(512))
    author: Mapped[str | None] = mapped_column(String(255))
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class UploadHistory(TimestampedBase):
    """
    V4 Book Upload History Log.
    Tracks all upload attempts via MiniApp or Bot.
    """

    __tablename__ = "upload_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    book_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(50), default="success")  # success, error
    final_path: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class LibraryCleanupLog(TimestampedBase):
    __tablename__ = "library_cleanup_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    performed_by: Mapped[int | None] = mapped_column(BigInteger)
    total_books_checked: Mapped[int] = mapped_column(default=0)
    missing_books_found: Mapped[int] = mapped_column(default=0)
    empty_series_removed: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")


class AILearningFeedback(TimestampedBase):
    __tablename__ = "ai_learning_feedback"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    original_name: Mapped[str | None] = mapped_column(String(255))
    proposed_name: Mapped[str | None] = mapped_column(String(255))
    final_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(50))
    ai_reason: Mapped[str | None] = mapped_column(Text)


class MetadataProposal(TimestampedBase):
    __tablename__ = "metadata_proposals"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    proposed_title_spanish: Mapped[str | None] = mapped_column(String(512))
    proposed_description: Mapped[str | None] = mapped_column(Text)
    proposed_slug: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    ai_confidence: Mapped[float | None] = mapped_column(Numeric)
    raw_response: Mapped[dict | None] = mapped_column(JSON, default=dict)
