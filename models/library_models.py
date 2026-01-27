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
)
from sqlalchemy.orm import relationship

from utils.helpers import limpiar_html_basico

from .base import Base


class TranslatorsGroup(Base):
    """
    Grupos de traducción y sus siglas para normalización de nombres de archivo.
    """
    __tablename__ = "translators_groups"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    siglas = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class SeriesMetadata(Base):
    """
    Centraliza la metadata de una serie para evitar redundancia en LocalBook.
    """
    __tablename__ = "series_metadata"

    id = Column(Integer, primary_key=True)
    series_name = Column(String(255), nullable=False)
    series_spanish = Column(String(255))
    series_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    author = Column(String(255))
    author_jap = Column(String(255))
    illustrator = Column(String(255))
    illustrator_jap = Column(String(255))
    
    description = Column(String(5000))
    tags = Column(JSON) # Géneros consolidados
    
    cover_url = Column(String(1024)) # Portada representativa de la serie
    book_count = Column(Integer, default=0)
    
    book_type = Column(String(100)) # Ej: Novela Ligera, Manga
    publisher = Column(String(255))
    
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    books = relationship("LocalBook", back_populates="series_info")


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
    user = relationship("User", foreign_keys=[telegram_id])
    
    # Metadata extraída (similar a LocalBook)
    title = Column(String(512), nullable=False)
    series = Column(String(255))
    series_spanish = Column(String(255))
    volume = Column(Float)
    author = Column(String(255))
    author_jap = Column(String(255))
    illustrator = Column(String(255))
    illustrator_jap = Column(String(255))
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
    path = Column(
        String(500), nullable=False, unique=True
    )  # Ej: "/home/zeepubs/drive/02-Publicaciones"
    last_scanned = Column(DateTime, default=None)

    books = relationship(
        "LocalBook", back_populates="source", cascade="all, delete-orphan"
    )


class LocalBook(Base):
    """
    Metadata enriquecida extraída directamente de los archivos EPUB.
    """

    __tablename__ = "local_books"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("library_sources.id"), nullable=False)

    # Identificación de archivo
    filepath = Column(String(1024), nullable=False, unique=True)
    filename = Column(String(512), nullable=False)
    file_size = Column(Integer)  # en bytes
    hash_md5 = Column(String(32))  # para detectar cambios sin re-escanear todo

    # Metadata del EPUB
    title = Column(String(512), nullable=False)
    romaji_title = Column(String(512))
    spanish_title = Column(String(512))  # Nueva columna
    english_title = Column(String(512))
    jap_title = Column(String(512))
    series = Column(String(255))
    series_spanish = Column(String(255)) # New column for Spanish series name from filename
    volume = Column(Float)  # Soporta 1, 1.5, etc
    edition = Column(String(255)) # Ej: "Honorificos", "Colector", etc.

    # Personas
    author = Column(String(255))
    author_jap = Column(String(255))
    illustrator = Column(String(255))
    illustrator_jap = Column(String(255))
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
    book_type = Column(String(100))  # Ej: Novela Ligera, Novela Web
    epub_version = Column(String(20))  # Ej: 2.0, 3.0

    # Advanced metrics
    word_count = Column(Integer)
    page_count = Column(Integer)
    reading_time = Column(Integer)  # in minutes

    # Ratings
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Contenido
    description = Column(String(5000))
    summary = Column(String(1024))  # AI generated catchy summary
    demographics = Column(JSON)  # Ej: ["Seinen", "Adultos"]
    tags = Column(JSON)  # Lista de géneros/etiquetas
    language = Column(String(10), default="es")
    
    # Edition Characteristics
    is_uncensored = Column(Integer, default=0) # 0 = No / Desconocido, 1 = Sí
    color_mode = Column(String(50)) # color, bw, mixed


    # UI - Cover Images (Progressive Quality Levels)
    cover_original = Column(String(1024))  # Original extracted from EPUB (full quality)
    cover_high = Column(String(1024))      # High quality: 800px width, 85% quality
    cover_medium = Column(String(1024))    # Medium quality: 400px width, 80% quality
    cover_low = Column(String(1024))       # Low quality: 200px width, 70% quality (default for UI)


    # Trazabilidad
    file_created_at = Column(DateTime)
    file_modified_at = Column(DateTime)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Identificadores estables basados en metadatos
    series_metadata_id = Column(Integer, ForeignKey("series_metadata.id"), index=True)
    series_hash = Column(String(64), index=True)  # Mantener por compatibilidad y búsqueda rápida
    book_hash = Column(String(64), index=True, unique=True)  # Identificador único del libro (antes content_hash)
    
    source = relationship("LibrarySource", back_populates="books")
    series_info = relationship("SeriesMetadata", back_populates="books")
    
    ratings = relationship("UserRating", back_populates="book", cascade="all, delete-orphan")
    downloads = relationship("UserDownload", back_populates="book", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": f"local_{self.id}",  # Prefijo para distinguir de Kavita IDs
            "hash": self.book_hash,
            "title": self.title,
            "author": self.author,
            "romajiTitle": self.romaji_title,
            "spanishTitle": self.spanish_title,
            "englishTitle": self.english_title,
            "japTitle": self.jap_title,
            "series": self.series,
            "seriesHash": self.series_hash,
            "seriesIndex": self.volume,
            "tags": self.tags,
            "demographics": self.demographics,
            "description": limpiar_html_basico(self.description),
            "description_clean": limpiar_html_basico(self.description), # Alias for backward compatibility
            "summary": self.summary or limpiar_html_basico(self.description),  # Prefer AI summary if available
            "fileSize": self.file_size,
            "modifiedAt": (
                self.file_modified_at.isoformat() if self.file_modified_at else None
            ),
            # Cover images - all quality levels
            "cover_original": self.cover_original,
            "cover_high": self.cover_high,
            "cover_medium": self.cover_medium,
            "cover_low": self.cover_low,
            # Backward compatibility aliases
            "cover": self.cover_low or self.cover_medium or self.cover_high or self.cover_original,
            "cover_thumb": self.cover_low,
            "filename": self.filename,
            "filepath": self.filepath,
            "downloadUrl": self.filepath,  # Ruta local para enviar_libro_directo
            "is_folder": False,
            # Enriched data
            "illustrator": self.illustrator,
            "translator": self.translator,
            "layoutBy": self.layout_by,
            "edition": self.edition,
            "publisher": self.publisher,
            "publishedAt": self.published_at,
            "modifiedAtOpf": self.modified_at_opf,
            "bookType": self.book_type,
            "isbn": self.isbn,
            "asin": self.asin,
            "uriId": self.uri_id,
            "epubVersion": self.epub_version,
            "wordCount": self.word_count,
            "pageCount": self.page_count,
            "english_title": self.english_title,
            "spanish_title": self.spanish_title,
            "jap_title": self.jap_title,
            "romaji_title": self.romaji_title,
            "author_jap": self.author_jap,
            "illustrator_jap": self.illustrator_jap,

            "readingTime": self.reading_time,
            "is_uncensored": bool(self.is_uncensored),
            "color_mode": self.color_mode,

            # Key mappings for consistency across services (Search, Telegram, Admin)
            "titulo": self.title,
            "autor": self.author,
            "categoria": self.book_type,
            "book_type": self.book_type,
            "book_hash": self.book_hash,
            "series_hash": self.series_hash,
            "titulo_serie": self.series,
            "series_spanish": self.series_spanish,
            "rating_average": self.rating_average,
            "rating_count": self.rating_count,
            "votes": self.rating_count,  # Alias
            
            # Frontend compatibility (CamelCase)
            "cleanTitle": self.series or self.english_title or (
                re.sub(r"\[.*?\]", "", self.title).strip() if self.title else ""
            ),
            "clean_title": self.series or self.english_title or (
                re.sub(r"\[.*?\]", "", self.title).strip() if self.title else ""
            )
        }


class UserRating(Base):
    """
    Votos individuales de usuarios para libros.
    """
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey("local_books.id"), nullable=True) # Opcional si el libro existe
    book_hash = Column(String(64), index=True, nullable=False)
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
    
    # Relación flexible: Preferimos ID si existe, pero guardamos hashes por si el libro se borra
    book_id = Column(Integer, ForeignKey("local_books.id"), nullable=True)
    book_hash = Column(String(64), index=True) # Persistencia histórica
    series_hash = Column(String(64), index=True)
    
    title = Column(String(512)) # Snapshot del título
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
    series_hash = Column(String(64), index=True, nullable=False)
    original_name = Column(String, nullable=False)
    proposed_name = Column(String, nullable=False)
    final_name = Column(String)
    status = Column(String(20), nullable=False) # accepted, rejected, edited, manual
    ai_reason = Column(String)
    user_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class MetadataProposal(Base):
    """
    Propuestas generadas por la IA en segundo plano que requieren aprobación admin.
    """
    __tablename__ = "metadata_proposals"

    id = Column(Integer, primary_key=True)
    series_hash = Column(String(64), index=True, nullable=False)
    
    # La propuesta completa en formato JSON (lo que devuelve AIService.analyze_series_for_updates)
    proposal_data = Column(JSON, nullable=False)
    
    status = Column(String(20), default="pending", index=True) # pending, approved, rejected
    type = Column(String(20), default="enrich", index=True) # enrich, merge
    secondary_hash = Column(String(64), index=True) # Para propuestas de MERGE (serie B)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


class ArchivedSeries(Base):
    """
    Guarda la información de las series que han sido eliminadas físicamente del disco.
    """
    __tablename__ = "archived_series"

    id = Column(Integer, primary_key=True)
    series_name = Column(String(255), nullable=False)
    series_spanish = Column(String(255))
    series_hash = Column(String(64), unique=True, index=True, nullable=False)
    
    author = Column(String(255))
    description = Column(String(5000))
    tags = Column(JSON)
    cover_url = Column(String(1024))
    
    book_type = Column(String(100))
    publisher = Column(String(255))
    
    archived_at = Column(DateTime, default=datetime.utcnow)
    original_series_id = Column(Integer) # ID original para referencia


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
    original_book_id = Column(Integer) # ID original para referencia
    reason = Column(String(255)) # Ej: "physically_deleted", "manual_archive"
