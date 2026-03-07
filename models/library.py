from datetime import datetime
from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Table, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, series_genres, series_demographics


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

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Hash de la serie
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    name_spanish: Mapped[Optional[str]] = mapped_column(String(512))
    name_english: Mapped[Optional[str]] = mapped_column(String(512))
    slug: Mapped[Optional[str]] = mapped_column(String(512), index=True)

    author: Mapped[Optional[str]] = mapped_column(String(255))
    author_jap: Mapped[Optional[str]] = mapped_column(String(255))
    illustrator: Mapped[Optional[str]] = mapped_column(String(255))
    illustrator_jap: Mapped[Optional[str]] = mapped_column(String(255))

    description: Mapped[Optional[str]] = mapped_column(Text)
    publisher: Mapped[Optional[str]] = mapped_column(String(255))
    book_type: Mapped[Optional[str]] = mapped_column(String(100))

    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)

    cover_url: Mapped[Optional[str]] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    books: Mapped[List["Book"]] = relationship(back_populates="series", cascade="all, delete-orphan")
    genres: Mapped[List[Genre]] = relationship(secondary=series_genres)
    demographics: Mapped[List[Demographic]] = relationship(secondary=series_demographics)
    media: Mapped[List["MediaAsset"]] = relationship(back_populates="series", cascade="all, delete-orphan")


class Book(Base):
    """
    Modelo unificado para Libros/Archivos individuales.
    """

    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Hash del libro
    series_id: Mapped[str] = mapped_column(ForeignKey("series.id"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("library_sources.id"))

    filepath: Mapped[str] = mapped_column(String(1024), unique=True)
    filename: Mapped[str] = mapped_column(String(512))
    file_size: Mapped[int] = mapped_column(Integer)
    hash_md5: Mapped[Optional[str]] = mapped_column(String(32))

    title: Mapped[str] = mapped_column(String(512))
    volume: Mapped[Optional[float]] = mapped_column(Float)
    edition: Mapped[Optional[str]] = mapped_column(String(255))

    translator: Mapped[Optional[str]] = mapped_column(String(255))
    layout_by: Mapped[Optional[str]] = mapped_column(String(255))

    language: Mapped[str] = mapped_column(String(10), default="es")
    is_uncensored: Mapped[bool] = mapped_column(Boolean, default=False)
    color_mode: Mapped[Optional[str]] = mapped_column(String(50))

    short_link: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    indexed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relaciones
    series: Mapped[Series] = relationship(back_populates="books")
    media: Mapped[List["MediaAsset"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class MediaAsset(Base):
    """
    Assets multimedia unificados.
    """

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(1024))

    series_id: Mapped[Optional[str]] = mapped_column(ForeignKey("series.id"))
    book_id: Mapped[Optional[str]] = mapped_column(ForeignKey("books.id"))

    series: Mapped[Optional[Series]] = relationship(back_populates="media")
    book: Mapped[Optional[Book]] = relationship(back_populates="media")
