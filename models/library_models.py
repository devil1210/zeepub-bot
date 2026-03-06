import re
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from utils.helpers import limpiar_html_basico

from .base import Base

# --- Tablas de Unión (Many-to-Many) ---

book_genres = Table(
    "book_genres",
    Base.metadata,
    Column("book_hash", String(64), ForeignKey("local_books.book_hash"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)

series_genres = Table(
    "series_genres",
    Base.metadata,
    Column("series_hash", String(64), ForeignKey("series_metadata.series_hash"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)

book_demographics = Table(
    "book_demographics",
    Base.metadata,
    Column("book_hash", String(64), ForeignKey("local_books.book_hash"), primary_key=True),
    Column("demographic_id", Integer, ForeignKey("demographics_list.id"), primary_key=True),
)

series_demographics = Table(
    "series_demographics",
    Base.metadata,
    Column("series_hash", String(64), ForeignKey("series_metadata.series_hash"), primary_key=True),
    Column("demographic_id", Integer, ForeignKey("demographics_list.id"), primary_key=True),
)


class TranslatorsGroup(Base):
    """
    Grupos de traducción y sus siglas para normalización de nombres de archivo.
    """

    __tablename__ = "translators_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    siglas = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class Genre(Base):
    """
    Tabla maestra de géneros (Action, Fantasy, etc.)
    """

    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class Demographic(Base):
    """
    Tabla maestra de demografías (Seinen, Shonen, etc.)
    """

    __tablename__ = "demographics_list"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class MediaAsset(Base):
    """
    Consolidación de assets multimedia (portadas, ilustraciones).
    """

    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True)
    asset_type = Column(String(50), nullable=False)  # original, high, medium, low
    url = Column(String(1024), nullable=False)

    book_hash = Column(String(64), ForeignKey("local_books.book_hash"), nullable=True)
    series_hash = Column(String(64), ForeignKey("series_metadata.series_hash"), nullable=True)

    book = relationship("LocalBook", back_populates="media")
    series = relationship("SeriesMetadata", back_populates="media")


class SeriesMetadata(Base):
    """
    Centraliza la metadata de una serie para evitar redundancia en LocalBook.
    """

    __tablename__ = "series_metadata"

    series_hash = Column(String(64), primary_key=True)
    series_name = Column(String(512), nullable=False)
    series_spanish = Column(String(512))
    series_english = Column(String(512))
    slug = Column(String(512), index=True)  # Slug persistente para URLs y referencias

    author = Column(String(255))
    author_jap = Column(String(255))
    illustrator = Column(String(255))
    illustrator_jap = Column(String(255))

    description = Column(String(5000))
    tags_json = Column("tags", JSONB)  # Legacy/Cache
    demographics_json = Column("demographics", JSONB)  # Legacy/Cache

    # Relaciones Normalizadas
    genres = relationship("Genre", secondary=series_genres, backref="series")
    demographics = relationship("Demographic", secondary=series_demographics, backref="series")
    media = relationship("MediaAsset", back_populates="series", cascade="all, delete-orphan")

    cover_url = Column(String(1024))  # Portada representativa de la serie
    book_count = Column(Integer, default=0)

    book_type = Column(String(255))  # Ej: Novela Ligera, Manga
    publisher = Column(String(255))

    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    books = relationship("LocalBook", back_populates="series_info", lazy="noload")

    def to_dict(self):
        return {
            "id": f"series_{self.series_hash}",
            "series_name": self.series_name,
            "series_spanish": self.series_spanish,
            "series_english": self.series_english,
            "slug": self.slug,
            "series_hash": self.series_hash,
            "author": self.author,
            "author_jap": self.author_jap,
            "illustrator": self.illustrator,
            "illustrator_jap": self.illustrator_jap,
            "description": limpiar_html_basico(self.description) if self.description else "",
            "tags": self.tags_json or [],
            "demographics": self.demographics_json or [],
            "cover_url": self.cover_url,
            "book_count": self.book_count,
            "book_type": self.book_type,
            "publisher": self.publisher,
            "rating_average": self.rating_average,
            "rating_count": self.rating_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UploadBook(Base):
    """
    Tabla temporal para procesar uploads antes de comparar con libros existentes.
    Usa la misma estructura que LocalBook para facilitar comparación.
    """

    __tablename__ = "upload_books"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)  # Usuario que subió el archivo
    original_filename = Column(String(512), nullable=False)
    temp_filepath = Column(String(1024), nullable=False)  # Ruta temporal del archivo

    # Relaciones
    user = relationship("User", back_populates="uploads", foreign_keys=[telegram_id])

    # Metadata extraída (similar a LocalBook)
    title = Column(String(512), nullable=False)
    volume = Column(Float)
    series = Column(String)
    illustrator = Column(String)
    illustrator_jap = Column(Text)
    author_jap = Column(Text)
    demographics = Column(JSON)
    author = Column(String)
    book_type = Column(String(100))
    translator = Column(String(255))
    layout_by = Column(String(255))
    language = Column(String(10), default="es")
    is_uncensored = Column(Integer, default=0)
    color_mode = Column(String(50))

    # Hashes para comparación
    book_hash = Column(String(64), nullable=False)
    series_hash = Column(String(64))

    # Estado del procesamiento
    identity_match = Column(String(10), default="False")  # Si coincide con libro existente
    path_collision = Column(String(10), default="False")  # Si hay colisión de ruta
    processed = Column(String(10), default="False")  # Si ya fue procesado

    # Metadata adicional en JSON
    upload_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class UploadHistory(Base):
    """
    Historial permanente de uploads (éxitos, fallos, duplicados).
    """

    __tablename__ = "upload_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, index=True, nullable=False)
    filename = Column(String(512), nullable=False)
    book_hash = Column(String(64))
    status = Column(String(50), nullable=False)  # success, error, duplicate_rejected
    final_path = Column(String(1024))
    error_message = Column(String(1024))
    created_at = Column(DateTime, default=datetime.utcnow)


class LibrarySource(Base):
    """
    Representa una carpeta raíz de libros configurable por el usuario.
    """

    __tablename__ = "library_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # Ej: "Novelas Ligeras"
    path = Column(String(500), nullable=False, unique=True)  # Ej: "/home/zeepubs/drive/02-Publicaciones"
    last_scanned = Column(DateTime, default=None)

    books = relationship("LocalBook", back_populates="source", cascade="all, delete-orphan", lazy="noload")


class LocalBook(Base):
    """
    Metadata enriquecida extraída directamente de los archivos EPUB.
    """

    __tablename__ = "local_books"

    book_hash = Column(String(64), primary_key=True)
    source_id = Column(Integer, ForeignKey("library_sources.id"), nullable=False)

    # Identificación de archivo
    filepath = Column(String(1024), nullable=False, unique=True)
    filename = Column(String(512), nullable=False)
    file_size = Column(Integer)  # en bytes
    hash_md5 = Column(String(32))  # para detectar cambios sin re-escanear todo

    # Metadata del EPUB
    title = Column(String(512), nullable=False)
    romaji_title = Column(String(512))
    spanish_title = Column(String(512))
    english_title = Column(String(512))
    jap_title = Column(String(512))
    volume = Column(Float)  # Soporta 1, 1.5, etc
    edition = Column(String(255))  # Ej: "Honorificos", "Colector", etc.

    # Advanced Metadata
    author = Column(String)
    illustrator = Column(String)
    illustrator_jap = Column(Text)
    author_jap = Column(Text)
    demographics_json = Column("demographics", JSONB)  # Legacy/Cache

    # Relaciones Normalizadas
    genres = relationship("Genre", secondary=book_genres, backref="books")
    demographics = relationship("Demographic", secondary=book_demographics, backref="books")
    media = relationship("MediaAsset", back_populates="book", cascade="all, delete-orphan")

    # Personas
    translator = Column(String(255))
    layout_by = Column(String(255))  # Maquetador
    publisher = Column(String(255))

    # Identificadores
    isbn = Column(String(50))
    asin = Column(String(50))  # Amazon ID
    uri_id = Column(String(255))  # URI identifer

    # Fechas y Tipo
    published_at = Column(String(100))
    modified_at_opf = Column(String(50))
    book_type = Column(String(100))  # Ej: Novela Ligera, Manga
    epub_version = Column(String(20))  # Ej: 2.0, 3.0

    # Advanced metrics
    word_count = Column(Integer)
    page_count = Column(Integer)
    reading_time = Column(Integer)  # in minutes

    # Ratings
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Contenido
    description = Column(Text)  # Renombrado de summary para coincidir con DB
    tags_json = Column("tags", JSON)  # Legacy/Cache
    language = Column(String(10), default="es")

    # Edition Characteristics
    is_uncensored = Column(Integer, default=0)  # 0 = No / Desconocido, 1 = Sí
    color_mode = Column(String(50))  # color, bw, mixed

    # UI - Cover Images (Progressive Quality Levels)
    cover_original = Column(String(1024))  # Original extracted from EPUB (full quality)
    cover_high = Column(String(1024))  # High quality: 800px width, 85% quality
    cover_medium = Column(String(1024))  # Medium quality: 400px width, 80% quality
    cover_low = Column(String(1024))  # Low quality: 200px width, 70% quality (default for UI)

    # Trazabilidad
    file_created_at = Column(DateTime)
    file_modified_at = Column(DateTime)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Identificadores estables basados en metadatos
    series_hash = Column(String(64), ForeignKey("series_metadata.series_hash"), index=True)
    short_link = Column(String(20), unique=True, index=True, nullable=True)  # Enlace corto descargas seguras

    source = relationship("LibrarySource", back_populates="books")
    series_info = relationship("SeriesMetadata", back_populates="books")

    ratings = relationship("UserRating", back_populates="book", cascade="all, delete-orphan", lazy="noload")
    downloads = relationship("UserDownload", back_populates="book", cascade="all, delete-orphan", lazy="noload")

    def to_dict(self):
        return {
            "id": f"local_{self.book_hash}",  # Prefijo para distinguir de Kavita IDs
            "hash": self.book_hash,
            "short_link": self.short_link,
            "title": self.title,
            "romajiTitle": self.romaji_title,
            "japTitle": self.jap_title,
            "series": self.series_info.series_name if getattr(self, "series_info", None) else None,
            "author": self.series_info.author if getattr(self, "series_info", None) else None,
            "slug": self.series_info.slug if getattr(self, "series_info", None) else None,
            "seriesHash": self.series_hash,
            "seriesIndex": self.volume,
            "volume": self.volume,
            "tags": (self.series_info.tags_json if getattr(self, "series_info", None) else []),
            "demographics": (self.series_info.demographics_json if getattr(self, "series_info", None) else []),
            "description": limpiar_html_basico(self.series_info.description)
            if getattr(self, "series_info", None) and self.series_info.description
            else "",
            "description_clean": limpiar_html_basico(self.series_info.description)
            if getattr(self, "series_info", None) and self.series_info.description
            else "",
            "summary": self.description
            or (
                limpiar_html_basico(self.series_info.description)
                if getattr(self, "series_info", None) and self.series_info.description
                else ""
            ),
            "fileSize": self.file_size,
            "file_size": self.file_size,
            "size": (
                f"{round(self.file_size / (1024 * 1024), 2)} MB" if self.file_size and self.file_size > 0 else "0 MB"
            ),
            "modifiedAt": (self.file_modified_at.isoformat() if self.file_modified_at else None),
            "modified_at": (self.file_modified_at.isoformat() if self.file_modified_at else None),
            # Portadas
            "cover_original": self.cover_original,
            "cover_high": self.cover_high,
            "cover_medium": self.cover_medium,
            "cover_low": self.cover_low,
            "cover": self.cover_low or self.cover_medium or self.cover_high or self.cover_original,
            "cover_thumb": self.cover_low,
            # Trazabilidad
            "filename": self.filename,
            "filepath": self.filepath,
            "is_folder": False,
            # Metadata enriquecida
            "illustrator": self.series_info.illustrator if getattr(self, "series_info", None) else None,
            "translator": self.translator,
            "group": self.translator,
            "layoutBy": self.layout_by,
            "layout_by": self.layout_by,
            "edition": self.edition,
            "publisher": self.publisher,
            "publishedAt": self.published_at,
            "published_at": self.published_at,
            "modifiedAtOpf": self.modified_at_opf,
            "modified_at_opf": self.modified_at_opf,
            "bookType": self.series_info.book_type if getattr(self, "series_info", None) else None,
            "book_type": self.series_info.book_type if getattr(self, "series_info", None) else None,
            "isbn": self.isbn,
            "asin": self.asin,
            "uriId": self.uri_id,
            "epubVersion": self.epub_version,
            "epub_version": self.epub_version,
            "wordCount": self.word_count,
            "word_count": self.word_count,
            "pageCount": self.page_count,
            "page_count": self.page_count,
            "author_jap": self.series_info.author_jap if getattr(self, "series_info", None) else None,
            "illustrator_jap": self.series_info.illustrator_jap if getattr(self, "series_info", None) else None,
            "language": self.language,
            "is_uncensored": self.is_uncensored == 1,
            "color_mode": self.color_mode,
            "volumeNumber": self.volume,
            "romaji_title": self.romaji_title,
            "readingTime": self.reading_time,
            "reading_time": self.reading_time,
            "book_hash": self.book_hash,
            "series_hash": self.series_hash,
            "rating_average": self.rating_average,
            "rating_count": self.rating_count,
            "votes": self.rating_count,
            "clean_title": (self.series_info.series_name if getattr(self, "series_info", None) else None)
            or (re.sub(r"\[.*?\]", "", self.title).strip() if self.title else ""),
            "cleanTitle": (self.series_info.series_name if getattr(self, "series_info", None) else None)
            or (re.sub(r"\[.*?\]", "", self.title).strip() if self.title else ""),
        }


class UserRating(Base):
    """
    Votos individuales de usuarios para libros.
    """

    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    book_hash = Column(String(64), ForeignKey("local_books.book_hash"), index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("LocalBook", back_populates="ratings")
    user = relationship("User", foreign_keys=[user_id])


class UserDownload(Base):
    """
    Historial de descargas de usuarios.
    """

    __tablename__ = "user_downloads"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)

    # Relación flexible: Usamos hashes como PKs
    book_hash = Column(String(64), ForeignKey("local_books.book_hash"), index=True)  # Persistencia histórica
    series_hash = Column(String(64), ForeignKey("series_metadata.series_hash"), index=True)

    title = Column(String(512))  # Snapshot del título
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    book = relationship("LocalBook", back_populates="downloads")
    user = relationship("User", foreign_keys=[user_id])


class DuplicateBook(Base):
    """
    Registra archivos EPUB que tienen el mismo book_hash que otro ya existente.
    """

    __tablename__ = "duplicate_books"

    id = Column(Integer, primary_key=True)
    book_hash = Column(String(64), index=True, nullable=False)

    # El archivo que ya estaba en la base de datos
    original_filepath = Column(String(1024))

    # El archivo nuevo que se intentó añadir y fue rechazado
    duplicate_filepath = Column(String(1024), nullable=False)

    # Metadata básica para visualización
    title = Column(String(512))
    author = Column(String(255))

    detected_at = Column(DateTime, default=datetime.utcnow)


class AILearningFeedback(Base):
    """
    Almacena el feedback de la IA sobre los nombres de series y decisiones de normalización.
    """

    __tablename__ = "ai_learning_feedback"

    id = Column(Integer, primary_key=True)
    series_hash = Column(String(64), ForeignKey("series_metadata.series_hash"), index=True, nullable=False)
    original_name = Column(String, nullable=False)
    proposed_name = Column(String, nullable=False)
    status = Column(String(20), nullable=False)  # accepted, rejected, edited, manual
    ai_reason = Column(String)
    user_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class MetadataProposal(Base):
    """
    Propuestas generadas por la IA en segundo plano que requieren aprobación admin.
    """

    __tablename__ = "metadata_proposals"

    id = Column(Integer, primary_key=True)
    series_hash = Column(String(64), ForeignKey("series_metadata.series_hash"), index=True, nullable=False)

    # La propuesta completa en formato JSON (lo que devuelve AIService.analyze_series)
    proposal_data = Column(JSON, nullable=False)

    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected
    type = Column(String(20), default="enrich", index=True)  # enrich, merge
    secondary_hash = Column(String(64), index=True)  # Para propuestas de MERGE (serie B)

    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class ArchivedSeries(Base):
    """
    Guarda la información de las series que han sido eliminadas físicamente del disco.
    """

    __tablename__ = "archived_series"

    id = Column(Integer, primary_key=True)
    series_name = Column(String(512), nullable=False)
    series_spanish = Column(String(512))
    series_english = Column(String(512))
    series_hash = Column(String(64), unique=True, index=True, nullable=False)

    cover_url = Column(String(1024))
    author = Column(String(255))
    author_jap = Column(Text)
    description = Column(Text)
    tags = Column(JSON)
    demographics = Column(JSON)
    book_type = Column(String(100))
    publisher = Column(String(255))
    slug = Column(String(255))

    archived_at = Column(DateTime, default=datetime.utcnow)
    original_series_id = Column(Integer)  # ID original para referencia


class ArchivedBook(Base):
    """
    Guarda la información de los libros que han sido eliminados físicamente del disco.
    """

    __tablename__ = "archived_books"

    id = Column(Integer, primary_key=True)
    series_hash = Column(String(64), index=True)
    book_hash = Column(String(64), index=True)

    title = Column(String(512), nullable=False)
    filename = Column(String(512))
    last_filepath = Column(String(1024))

    volume = Column(Float)
    author = Column(String(255))
    book_type = Column(String(100))

    archived_at = Column(DateTime, default=datetime.utcnow)
    original_book_id = Column(Integer)  # ID original para referencia
    reason = Column(String(100))  # Ej: "physically_deleted", "manual_archive"


class LibraryCleanupLog(Base):
    """
    Registro histórico de las operaciones de limpieza y mantenimiento de la librería.
    """

    __tablename__ = "library_cleanup_logs"

    id = Column(Integer, primary_key=True)
    performed_by = Column(Integer)  # user_id
    total_books_checked = Column(Integer, default=0)
    missing_books_found = Column(Integer, default=0)
    empty_series_removed = Column(Integer, default=0)
    status = Column(String(50))  # "success", "error"
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
