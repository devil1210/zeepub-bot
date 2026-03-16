import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(512))
    author: Mapped[str | None] = mapped_column(String(512))
    tags: Mapped[list[str] | None] = mapped_column(JSONB)
    rating_average: Mapped[float] = mapped_column(Numeric(3, 2), default=0.0)
    rating_count: Mapped[int] = mapped_column(default=0)
    book_count: Mapped[int] = mapped_column(default=0)
    book_type: Mapped[str | None] = mapped_column(String(50))
    publisher: Mapped[str | None] = mapped_column(String(255))
    slug: Mapped[str | None] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default="reading")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    source: Mapped["LibrarySource"] = relationship(back_populates="series")
    books: Mapped[list["Book"]] = relationship(back_populates="series", cascade="all, delete-orphan")

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
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(BigInteger)
    extension: Mapped[str] = mapped_column(String(10))
    volume_number: Mapped[float] = mapped_column(Numeric, nullable=False)
    title: Mapped[str | None] = mapped_column(String(512))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    is_published: Mapped[bool] = mapped_column(default=False)
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

    @series_hash.expression
    def series_hash(cls):
        return select(Series.hash).where(Series.id == cls.series_id).label("series_hash")

    @hybrid_property
    def source_id(self) -> uuid.UUID | None:
        return self.series.source_id if self.series else None

    @source_id.expression
    def source_id(cls):
        return select(Series.source_id).where(Series.id == cls.series_id).label("source_id")

    @hybrid_property
    def author(self) -> str:
        return self.series.author if self.series else "Unknown"

    @author.expression
    def author(cls):
        return select(Series.author).where(Series.id == cls.series_id).label("author")

    @hybrid_property
    def book_type(self) -> str:
        return self.series.book_type if self.series else "Light Novel"

    @book_type.expression
    def book_type(cls):
        return select(Series.book_type).where(Series.id == cls.series_id).label("book_type")


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
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class UploadBook(TimestampedBase):
    __tablename__ = "upload_books"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, processed, failed
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
