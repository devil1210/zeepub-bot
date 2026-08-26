from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
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

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, autoincrement=False, nullable=False
    )  # Hash de la serie
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

    rating_average: Mapped[float] = mapped_column(
        "rating_avg", Float, default=0.0, nullable=False
    )
    rating_count: Mapped[int] = mapped_column(
        "rating_count", Integer, default=0, nullable=False
    )
    book_count: Mapped[int] = mapped_column(
        "book_count", Integer, default=0, nullable=True
    )

    @hybrid_property
    def rating_avg(self) -> float:
        """Alias de compatibilidad para rating_average."""
        return self.rating_average

    @rating_avg.setter
    def rating_avg(self, value: float):
        self.rating_average = value

    @rating_avg.expression
    def rating_avg(cls):
        return cls.rating_average

    tags_json: Mapped[list | None] = mapped_column(JSONB)
    demographics_json: Mapped[list | None] = mapped_column(JSONB)

    cover_url: Mapped[str | None] = mapped_column(String(1024))
    fb_album_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

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
        """Nombre de la serie con fallback inteligente."""
        return self.name

    @series_name.setter
    def series_name(self, value: str):
        self.name = value

    @series_name.expression
    def series_name(cls):
        return cls.name

    @hybrid_property
    def series_spanish(self) -> str:
        """Nombre en español con fallback al nombre original."""
        return self.name_spanish or self.name

    @series_spanish.setter
    def series_spanish(self, value: str | None):
        self.name_spanish = value

    @series_spanish.expression
    def series_spanish(cls):
        return cls.name_spanish

    @hybrid_property
    def series_english(self) -> str:
        """Nombre en inglés con fallback al nombre original."""
        return self.name_english or self.name

    @series_english.setter
    def series_english(self, value: str | None):
        self.name_english = value

    @series_english.expression
    def series_english(cls):
        return cls.name_english

    # Relaciones
    books: Mapped[list["Book"]] = relationship(
        back_populates="series_info", cascade="all, delete-orphan"
    )
    genres: Mapped[list[Genre]] = relationship(secondary=series_genres, lazy="selectin")
    demographics: Mapped[list[Demographic]] = relationship(
        secondary=series_demographics, lazy="selectin"
    )
    media: Mapped[list["MediaAsset"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    aliases: Mapped[list["SeriesAlias"]] = relationship(
        back_populates="series", cascade="all, delete-orphan", lazy="selectin"
    )


class SeriesAlias(Base):
    """
    Tabla de alias de títulos alternativos para la deduplicación de series.
    """

    __tablename__ = "series_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("series.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(
        String(512), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    series: Mapped["Series"] = relationship(back_populates="aliases")


# Alias para compatibilidad con código legacy
SeriesMetadata = Series


class LibrarySource(Base):
    """
    Representa una carpeta raíz de libros configurable por el usuario.
    """

    __tablename__ = "library_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(1024), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    books: Mapped[list["Book"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class Book(Base):
    """
    Modelo unificado para Libros/Archivos individuales.
    """

    __tablename__ = "books"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, autoincrement=False, nullable=False
    )  # Hash / UUID del libro
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

    # Créditos individuales en texto
    translator: Mapped[str | None] = mapped_column(String(255))
    layout_by: Mapped[str | None] = mapped_column(String(255))
    editor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Vinculación por UUID de Libro a Grupos Oficiales
    translator_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("translators_groups.id"), nullable=True
    )
    editor_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("translators_groups.id"), nullable=True
    )
    layout_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("translators_groups.id"), nullable=True
    )

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
    rating_average: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    reading_time: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    modified_at_opf: Mapped[datetime | None] = mapped_column(DateTime)

    cover_low: Mapped[str | None] = mapped_column(String(1024))
    cover_medium: Mapped[str | None] = mapped_column(String(1024))
    cover_high: Mapped[str | None] = mapped_column(String(1024))
    cover_original: Mapped[str | None] = mapped_column(String(1024))

    short_link: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    fb_post_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fb_photo_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tg_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tg_chat_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    indexed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Propiedades híbridas
    @hybrid_property
    def book_hash(self) -> str:
        """Alias semántico para el hash del libro."""
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

    @property
    def series(self) -> "Series":
        """Alias de compatibilidad para series_info."""
        return self.series_info

    @series.setter
    def series(self, value: "Series"):
        self.series_info = value

    # Relaciones
    translator_group: Mapped["TranslatorsGroup | None"] = relationship(
        foreign_keys=[translator_group_id], lazy="selectin"
    )
    editor_group: Mapped["TranslatorsGroup | None"] = relationship(
        foreign_keys=[editor_group_id], lazy="selectin"
    )
    layout_group: Mapped["TranslatorsGroup | None"] = relationship(
        foreign_keys=[layout_group_id], lazy="selectin"
    )
    workgroups: Mapped[list["BookWorkgroup"]] = relationship(
        back_populates="book", cascade="all, delete-orphan", lazy="selectin"
    )
    series_info: Mapped[Series] = relationship(back_populates="books")
    genres: Mapped[list[Genre]] = relationship(secondary="book_genres", lazy="selectin")
    demographics: Mapped[list[Demographic]] = relationship(
        secondary="book_demographics", lazy="selectin"
    )
    media: Mapped[list["MediaAsset"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    source: Mapped[LibrarySource] = relationship(back_populates="books")
    ratings: Mapped[list["UserRating"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )
    downloads: Mapped[list["UserDownload"]] = relationship(
        back_populates="book", cascade="all, delete-orphan"
    )


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
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), index=True
    )
    book_id: Mapped[str] = mapped_column(String(64), ForeignKey("books.id"), index=True)
    book_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    book: Mapped[Book] = relationship(back_populates="ratings")


class UserDownload(Base):
    """
    Historial de descargas de usuarios.
    """

    __tablename__ = "user_downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), index=True
    )
    book_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("books.id"), index=True
    )
    series_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("series.id"), index=True
    )

    book_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    series_hash: Mapped[str | None] = mapped_column(String(64), index=True)

    title: Mapped[str | None] = mapped_column(String(512))
    downloaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    book: Mapped[Book | None] = relationship(back_populates="downloads")
    series: Mapped[Series | None] = relationship()


class BookWorkgroup(Base):
    """
    Asociación de grupos traductores/editores/maquetadores vinculados directamente por UUID de Libro
    (ERD zeepubs_server: VOLUME_WORKGROUP).
    Roles soportados: 'translator', 'editor', 'layout', 'proofreader', 'raw', etc.
    """

    __tablename__ = "book_workgroups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[str] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
    )
    workgroup_id: Mapped[int] = mapped_column(
        ForeignKey("translators_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), default="translator", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    book: Mapped["Book"] = relationship(back_populates="workgroups")
    workgroup: Mapped["TranslatorsGroup"] = relationship(lazy="selectin")


class GroupContactLink(Base):
    """
    Enlaces de contacto oficiales de grupos traductores (ERD zeepubs_server: GROUP_CONTACT_LINK).
    """

    __tablename__ = "group_contact_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("translators_groups.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    platform: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # website, facebook, discord, patreon, twitter
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    group: Mapped["TranslatorsGroup"] = relationship(back_populates="contact_links")


class TranslatorsGroup(Base):
    """
    Grupos de traducción y enlaces oficiales (ERD zeepubs_server: WORKGROUP).
    """

    __tablename__ = "translators_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    siglas: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    contact_links: Mapped[list[GroupContactLink]] = relationship(
        back_populates="group", cascade="all, delete-orphan", lazy="selectin"
    )

    def get_preferred_link(self) -> str | None:
        """
        Devuelve el enlace preferido según el orden de prioridad:
        1. Website / Web Oficial
        2. Facebook
        3. Discord
        4. Patreon / Otros
        """
        priority = ["web", "site", "pagina", "face", "fb", "disc", "patr", "twit", "x"]
        links = {
            link.platform.lower().strip(): link.url
            for link in self.contact_links
            if link.url
        }
        for p in priority:
            for platform, url in links.items():
                if p in platform:
                    return url
        if self.contact_links:
            return self.contact_links[0].url
        return None

    def get_links_dict(self) -> dict[str, str]:
        """Devuelve diccionario con claves estandarizadas: web, fb, discord, patreon, twitter."""
        result: dict[str, str] = {}
        for link in self.contact_links:
            if not link.url:
                continue
            plat = link.platform.lower().strip()
            if any(k in plat for k in ["web", "site", "pagina"]):
                result["web"] = link.url
            elif any(k in plat for k in ["face", "fb"]):
                result["fb"] = link.url
            elif "disc" in plat:
                result["discord"] = link.url
            elif "patr" in plat:
                result["patreon"] = link.url
            elif any(k in plat for k in ["twit", "x"]):
                result["twitter"] = link.url
            else:
                result[plat] = link.url
        return result


# Alias para alineación con el ERD de zeepubs_server
Workgroup = TranslatorsGroup


class UploadBook(Base):
    """
    Tabla temporal para procesar uploads.
    """

    __tablename__ = "upload_books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id"), index=True
    )
    original_filename: Mapped[str] = mapped_column(String(512))
    temp_filepath: Mapped[str] = mapped_column(String(1024))

    title: Mapped[str] = mapped_column(String(512))
    series: Mapped[str | None] = mapped_column(String(255), nullable=True)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_jap: Mapped[str | None] = mapped_column(String(255), nullable=True)
    illustrator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    illustrator_jap: Mapped[str | None] = mapped_column(String(255), nullable=True)
    book_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    translator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    layout_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), default="es")
    is_uncensored: Mapped[int] = mapped_column(Integer, default=0)
    color_mode: Mapped[str | None] = mapped_column(String(50), default="bw")

    book_hash: Mapped[str] = mapped_column(String(64), index=True)
    series_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    identity_match: Mapped[str] = mapped_column(String(10), default="False")
    path_collision: Mapped[str] = mapped_column(String(10), default="False")
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    upload_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    @hybrid_property
    def user_id(self) -> int:
        return self.telegram_id

    @user_id.setter
    def user_id(self, value: int):
        self.telegram_id = value

    @user_id.expression
    def user_id(cls):
        return cls.telegram_id


class UploadHistory(Base):
    """
    Historial permanente de uploads.
    """

    __tablename__ = "upload_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    filename: Mapped[str] = mapped_column(String(512))
    book_hash: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(50)
    )  # success, error, duplicate_rejected
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
    series_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("series.id"), index=True
    )
    original_name: Mapped[str] = mapped_column(String)
    proposed_name: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(
        String(20)
    )  # accepted, rejected, edited, manual
    ai_reason: Mapped[str | None] = mapped_column(String)
    user_reason: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class MetadataProposal(Base):
    """
    Propuestas de la IA que requieren aprobación.
    """

    __tablename__ = "metadata_proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey("series.id"), index=True
    )
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
    author: Mapped[str | None] = mapped_column(String(255))
    book_type: Mapped[str | None] = mapped_column(String(100))

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
