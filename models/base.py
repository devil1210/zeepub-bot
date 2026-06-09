from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """
    Clase base para todos los modelos de ZeePub v4.0.
    """

    def to_dict(self):
        """Convierte el modelo a un diccionario para serialización."""
        res = {}
        for prop in self.__class__.__mapper__.column_attrs:
            res[prop.key] = getattr(self, prop.key)

        # Incluir hybrid properties y properties standard
        from sqlalchemy.ext.hybrid import hybrid_property

        for attr in dir(self.__class__):
            if attr.startswith("_") or attr == "awaitable_attrs":
                continue

            # Obtener el descriptor de la clase
            cls_attr = getattr(self.__class__, attr, None)
            if isinstance(cls_attr, (property, hybrid_property)) or attr.endswith(
                "_hash"
            ):
                try:
                    val = getattr(self, attr)
                    if not callable(val):
                        if isinstance(val, Base):
                            continue
                        res[attr] = val
                except Exception:
                    pass

        # Incluir atributos de instancia dinámicos (como download_count)
        for key, val in self.__dict__.items():
            if not key.startswith("_") and key not in res:
                if isinstance(val, Base):
                    continue
                # Sanitizar colecciones (listas, tuplas, conjuntos) que contengan modelos Base (como Genre/Demographic)
                if isinstance(val, (list, tuple, set)):
                    if any(isinstance(item, Base) for item in val):
                        cleaned_list = []
                        for item in val:
                            if isinstance(item, Base):
                                if hasattr(item, "name"):
                                    cleaned_list.append(item.name)
                                elif hasattr(item, "to_dict"):
                                    cleaned_list.append(item.to_dict())
                                else:
                                    cleaned_list.append(str(item))
                            else:
                                cleaned_list.append(item)
                        res[key] = cleaned_list
                        continue
                res[key] = val

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
