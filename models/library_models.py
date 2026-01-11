from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


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
    english_title = Column(String(512))
    series = Column(String(255))
    series_clean = Column(String(255))
    volume = Column(Float)  # Soporta 1, 1.5, etc

    # Personas
    author = Column(String(255))
    illustrator = Column(String(255))
    translator = Column(String(255))
    layout_by = Column(String(255))  # Maquetador
    publisher = Column(String(255))

    # Identificadores
    isbn = Column(String(20))
    asin = Column(String(50))  # Amazon ID
    uri_id = Column(String(512))  # URI identifer

    # Fechas y Tipo
    published_at = Column(String(50))
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

    # UI
    cover_path = Column(
        String(1024)
    )  # Ruta a la miniatura extraída en data/library/covers/

    # Trazabilidad
    file_created_at = Column(DateTime)
    file_modified_at = Column(DateTime)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Identificadores estables basados en metadatos
    series_hash = Column(String(64), index=True)  # Agrupa volúmenes de la misma serie/tipo
    content_hash = Column(String(64), index=True, unique=True)  # Identifica el EPUB específico (incluye volumen y traductor)

    source = relationship("LibrarySource", back_populates="books")

    def to_dict(self):
        return {
            "id": f"local_{self.id}",  # Prefijo para distinguir de Kavita IDs
            "hash": self.content_hash,
            "title": self.title,
            "author": self.author,
            "romaji": self.romaji_title,
            "englishTitle": self.english_title,
            "series": self.series,
            "series_clean": self.series_clean,
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
            "cover": self.cover_path,  # Alias para compatibilidad
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

            "readingTime": self.reading_time,
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
    user_id = Column(Integer, nullable=False)
    book_id = Column(Integer, ForeignKey("local_books.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("LocalBook")
