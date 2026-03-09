from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """
    Clase base para todos los modelos de ZeePub v4.0.
    """

    def to_dict(self):
        """Convierte el modelo a un diccionario para serialización."""
        res = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        # Incluir hybrid properties si es necesario (ej. series_hash, book_hash)
        for attr in dir(self.__class__):
            if isinstance(getattr(self.__class__, attr), property) or attr.endswith("_hash"):
                try:
                    val = getattr(self, attr)
                    if not callable(val) and not attr.startswith("_"):
                        res[attr] = val
                except Exception:
                    pass
        return res


# --- Tablas de Unión Globales (Para evitar re-definición en imports) ---

series_genres = Table(
    "series_genres",
    Base.metadata,
    Column("series_id", String(64), ForeignKey("series.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)

series_demographics = Table(
    "series_demographics",
    Base.metadata,
    Column("series_id", String(64), ForeignKey("series.id"), primary_key=True),
    Column("demographic_id", Integer, ForeignKey("demographics.id"), primary_key=True),
)

book_genres = Table(
    "book_genres",
    Base.metadata,
    Column("book_id", String(64), ForeignKey("books.id"), primary_key=True),
    Column("genre_id", Integer, ForeignKey("genres.id"), primary_key=True),
)

book_demographics = Table(
    "book_demographics",
    Base.metadata,
    Column("book_id", String(64), ForeignKey("books.id"), primary_key=True),
    Column("demographic_id", Integer, ForeignKey("demographics.id"), primary_key=True),
)
