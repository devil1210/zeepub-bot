from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Table, Column, String, ForeignKey, Integer


class Base(AsyncAttrs, DeclarativeBase):
    """
    Clase base para todos los modelos de ZeePub v4.0.
    """

    pass


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
