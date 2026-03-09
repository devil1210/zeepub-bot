from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, series_demographics, series_genres


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Demographic(Base):
    __tablename__ = "demographics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Series(Base):
    """
    Modelo unificado para Series (Metadata maestra).
    """

    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, autoincrement=False)  # Hash de la serie
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    name_spanish: Mapped[str | None] = mapped_column(String(512))
    name_english: Mapped[str | None] = mapped_column(String(512))
    slug: Mapped[str | None] = mapped_column(String(512), index=True)

    author: Mapped[str | None] = mapped_column(String(255))
    author_jap: Mapped[str | None] = mapped_column(String(255))
    illustrator: Mapped[str | None] = mapped_column(String(255))
    illustrator_jap: Mapped[str | None] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text)
    publisher: Mapped[str | None] = mapped_column(String(255))
    book_type: Mapped[str | None] = mapped_column(String(100))

    rating_average: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    book_count: Mapped[int] = mapped_column(Integer, default=0)

    tags_json: Mapped[list | None] = mapped_column(JSONB)
    demographics_json: Mapped[list | None] = mapped_column(JSONB)

    cover_url: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    @hybrid_property
    def series_hash(self) -> str:
        """Alias semántico para el ID de la serie (que es su hash)."""
        return self.id

    @series_hash.setter
    def series_hash(self, value: str):
        self.id = value

    @series_hash.expression
    def series_hash(cls):
        return cls.id

    @hybrid_property
    def series_name(self) -> str:
        return self.name

    @series_name.setter
    def series_name(self, value: str):
        self.name = value

    @series_name.expression
    def series_name(cls):
        return cls.name

    @hybrid_property
    def series_spanish(self) -> str | None:
        return self.name_spanish

    @series_spanish.setter
    def series_spanish(self, value: str | None):
        self.name_spanish = value

    @series_spanish.expression
    def series_spanish(cls):
        return cls.name_spanish

    @hybrid_property
    def series_english(self) -> str | None:
        return self.name_english

    @series_english.setter
    def series_english(self, value: str | None):
        self.name_english = value

    @series_english.expression
    def series_english(cls):
        return cls.name_english

    # Relaciones
    books: Mapped[list["Book"]] = relationship(back_populates="series_info", cascade="all, delete-orphan")
    genres: Mapped[list[Genre]] = relationship(secondary=series_genres)
    demographics: Mapped[list[Demographic]] = relationship(secondary=series_demographics)
    media: Mapped[list["MediaAsset"]] = relationship(back_populates="series", cascade="all, delete-orphan")


# Alias para compatibilidad con código legacy
SeriesMetadata = Series


class LibrarySource(Base):
    """
    Representa una carpeta raíz de libros configurable por el usuario.
    """

    __tablename__ = "library_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    last_scanned: Mapped[datetime | None] = mapped_column(default=None)

    books: Mapped[list["Book"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class Book(Base):
    """
    Modelo unificado para Libros/Archivos individuales.
    """

    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, autoincrement=False)  # Hash del libro
    series_id: Mapped[str] = mapped_column(ForeignKey("series.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("library_sources.id"))

    filepath: Mapped[str] = mapped_column(String(1024), unique=True)
    filename: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(Integer)
    hash_md5: Mapped[str | None] = mapped_column(String(32))
    file_modified_at: Mapped[datetime | None] = mapped_column(DateTime)

    title: Mapped[str] = mapped_column(String(512))
    volume: Mapped[float | None] = mapped_column(Float)
    edition: Mapped[str | None] = mapped_column(String(255))

    translator: Mapped[str | None] = mapped_column(String(255))
    layout_by: Mapped[str | None] = mapped_column(String(255))

    author_jap: Mapped[str | None] = mapped_column(String(255))
    illustrator: Mapped[str | None] = mapped_column(String(255))
    illustrator_jap: Mapped[str | None] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255))
    publisher: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    spanish_title: Mapped[str | None] = mapped_column(String(512))
    romaji_title: Mapped[str | None] = mapped_column(String(512))
    english_title: Mapped[str | None] = mapped_column(String(512))
    series_spanish: Mapped[str | None] = mapped_column(String(512))
    series_english: Mapped[str | None] = mapped_column(String(512))

    tags_json: Mapped[list | None] = mapped_column(JSONB)
    demographics_json: Mapped[list | None] = mapped_column(JSONB)

    language: Mapped[str] = mapped_column(String(10), default="es")
    is_uncensored: Mapped[bool] = mapped_column(Boolean, default=False)
    color_mode: Mapped[str | None] = mapped_column(String(50))

    isbn: Mapped[str | None] = mapped_column(String(50))
    asin: Mapped[str | None] = mapped_column(String(50))
    epub_version: Mapped[str | None] = mapped_column(String(20))
    word_count: Mapped[int | None] = mapped_column(Integer)
    page_count: Mapped[int | None] = mapped_column(Integer)
    reading_time: Mapped[int | None] = mapped_column(Integer)
    modified_at_opf: Mapped[datetime | None] = mapped_column(DateTime)

    cover_low: Mapped[str | None] = mapped_column(String(1024))
    cover_medium: Mapped[str | None] = mapped_column(String(1024))
    cover_high: Mapped[str | None] = mapped_column(String(1024))
    cover_original: Mapped[str | None] = mapped_column(String(1024))

    short_link: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    indexed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    @hybrid_property
    def book_hash(self) -> str:
        """Alias para el hash del libro (id) para compatibilidad v3/Legacy."""
        return self.id

    @book_hash.setter
    def book_hash(self, value: str):
        self.id = value

    @book_hash.expression
    def book_hash(cls):
        return cls.id

    @hybrid_property
    def series_hash(self) -> str:
        """Alias semántico para el hash de la serie vinculada."""
        return self.series_id

    @series_hash.setter
    def series_hash(self, value: str):
        self.series_id = value

    @series_hash.expression
    def series_hash(cls):
        return cls.series_id

    # Relaciones
    series_info: Mapped[Series] = relationship(back_populates="books")
    genres: Mapped[list[Genre]] = relationship(secondary="book_genres")
    demographics: Mapped[list[Demographic]] = relationship(secondary="book_demographics")
    media: Mapped[list["MediaAsset"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    source: Mapped[LibrarySource] = relationship(back_populates="books")
    ratings: Mapped[list["UserRating"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    downloads: Mapped[list["UserDownload"]] = relationship(back_populates="book", cascade="all, delete-orphan")


# Alias para compatibilidad con código legacy
LocalBook = Book


class MediaAsset(Base):
    """
    Assets multimedia unificados.
    """

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(1024))

    series_id: Mapped[str | None] = mapped_column(ForeignKey("series.id"))
    book_id: Mapped[str | None] = mapped_column(ForeignKey("books.id"))

    series: Mapped[Series | None] = relationship(back_populates="media")
    book: Mapped[Book | None] = relationship(back_populates="media")


class UserRating(Base):
    """
    Votos individuales de usuarios para libros.
    """

    __tablename__ = "user_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    book_id: Mapped[str] = mapped_column(String(64), ForeignKey("books.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    book: Mapped[Book] = relationship(back_populates="ratings")


class UserDownload(Base):
    """
    Historial de descargas de usuarios.
    """

    __tablename__ = "user_downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    book_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("books.id"), index=True)
    series_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("series.id"), index=True)

    title: Mapped[str | None] = mapped_column(String(512))
    downloaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    book: Mapped[Book | None] = relationship(back_populates="downloads")
    series: Mapped[Series | None] = relationship()


class TranslatorsGroup(Base):
    """
    Grupos de traducción y sus siglas para normalización de nombres de archivo.
    """

    __tablename__ = "translators_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    siglas: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class UploadBook(Base):
    """
    Tabla temporal para procesar uploads.
    """

    __tablename__ = "upload_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    original_filename: Mapped[str] = mapped_column(String(512))
    temp_filepath: Mapped[str] = mapped_column(String(1024))

    title: Mapped[str] = mapped_column(String(512))
    volume: Mapped[float | None] = mapped_column(Float)
    series_id: Mapped[str | None] = mapped_column(String(64))

    book_hash: Mapped[str] = mapped_column(String(64))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class UploadHistory(Base):
    """
    Historial permanente de uploads.
    """

    __tablename__ = "upload_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    filename: Mapped[str] = mapped_column(String(512))
    book_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(50))  # success, error, duplicate_rejected
    final_path: Mapped[str | None] = mapped_column(String(1024))
    error_message: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class DuplicateBook(Base):
    """
    Registra archivos EPUB duplicados.
    """

    __tablename__ = "duplicate_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_hash: Mapped[str] = mapped_column(String(64), index=True)
    original_filepath: Mapped[str | None] = mapped_column(String(1024))
    duplicate_filepath: Mapped[str] = mapped_column(String(1024))
    title: Mapped[str | None] = mapped_column(String(512))
    author: Mapped[str | None] = mapped_column(String(255))
    detected_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class AILearningFeedback(Base):
    """
    Feedback de la IA sobre normalización.
    """

    __tablename__ = "ai_learning_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_hash: Mapped[str] = mapped_column(String(64), ForeignKey("series.id"), index=True)
    original_name: Mapped[str] = mapped_column(String)
    proposed_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String(20))  # accepted, rejected, edited, manual
    ai_reason: Mapped[str | None] = mapped_column(String)
    user_reason: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class MetadataProposal(Base):
    """
    Propuestas de la IA que requieren aprobación.
    """

    __tablename__ = "metadata_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_hash: Mapped[str] = mapped_column(String(64), ForeignKey("series.id"), index=True)
    proposal_data: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    type: Mapped[str] = mapped_column(String(20), default="enrich", index=True)
    secondary_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)


class ArchivedSeries(Base):
    """
    Series eliminadas físicamente.
    """

    __tablename__ = "archived_series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_name: Mapped[str] = mapped_column(String(512))
    series_spanish: Mapped[str | None] = mapped_column(String(512))
    series_english: Mapped[str | None] = mapped_column(String(512))
    series_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    cover_url: Mapped[str | None] = mapped_column(String(1024))
    author: Mapped[str | None] = mapped_column(String(255))

    description: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list | None] = mapped_column(JSONB)
    book_type: Mapped[str | None] = mapped_column(String(100))
    publisher: Mapped[str | None] = mapped_column(String(255))
    original_series_id: Mapped[str | None] = mapped_column(String(64))
    slug: Mapped[str | None] = mapped_column(String(512))

    archived_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class ArchivedBook(Base):
    """
    Libros eliminados físicamente.
    """

    __tablename__ = "archived_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    book_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512))
    filename: Mapped[str | None] = mapped_column(String(512))
    last_filepath: Mapped[str | None] = mapped_column(String(1024))
    file_size: Mapped[int | None] = mapped_column(Integer)
    hash_md5: Mapped[str | None] = mapped_column(String(32))

    archived_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class LibraryCleanupLog(Base):
    """
    Mantenimiento de la librería.
    """

    __tablename__ = "library_cleanup_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    performed_by: Mapped[int | None] = mapped_column(Integer)
    total_books_checked: Mapped[int] = mapped_column(Integer, default=0)
    missing_books_found: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
