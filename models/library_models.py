from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


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
    volume = Column(Float)  # Soporta 1, 1.5, etc

    # Personas
    author = Column(String(255))
    illustrator = Column(String(255))
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
    demographics = Column(JSON)  # Ej: ["Seinen", "Adultos"]
    tags = Column(JSON)  # Lista de géneros/etiquetas
    language = Column(String(10), default="es")


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
    series_hash = Column(String(64), index=True)  # Agrupa volúmenes de la misma serie/tipo
    book_hash = Column(String(64), index=True, unique=True)  # Identificador único del libro (antes content_hash)
    
    # Property for backward compatibility
    @property
    def content_hash(self):
        return self.book_hash

    @content_hash.setter
    def content_hash(self, value):
        self.book_hash = value

    source = relationship("LibrarySource", back_populates="books")

    def to_dict(self):
        return {
            "id": f"local_{self.id}",  # Prefijo para distinguir de Kavita IDs
            "hash": self.book_hash,
            "content_hash": self.book_hash,
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
            "description": self.description,
            "summary": self.description,  # Alias para compatibilidad
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
            "downloadUrl": self.filepath,  # Ruta local para enviar_libro_directo
            "is_folder": False,
            # Enriched data
            "illustrator": self.illustrator,
            "translator": self.translator,
            "layoutBy": self.layout_by,
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

            "readingTime": self.reading_time,

            # Key mappings for telegram_service / search consistency
            "titulo": self.title,
            "autor": self.author,
            "categoria": self.book_type,
            "book_type": self.book_type,
            "clean_title": self.series or self.english_title or self.title,
            "series_hash": self.series_hash,
            "titulo_serie": self.series,
            "rating_average": self.rating_average,
            "rating_count": self.rating_count,
            "votes": self.rating_count,  # Alias
        }


class UserRating(Base):
    """
    Votos individuales de usuarios para libros.
    """
    __tablename__ = "user_ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    book_id = Column(Integer, ForeignKey("local_books.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("LocalBook")


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
    book = relationship("LocalBook")
    # user = relationship("User") # Definido en user_models (back_populates no necesario aquí si no se usa)
