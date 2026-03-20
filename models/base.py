from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import JSON, TypeDecorator


class CompatibleJSONB(TypeDecorator):
    """
    Usa JSON base para máxima compatibilidad entre motores (SQLite/Postgres).
    En Postgres, SQLAlchemy lo mapeará a JSON nativo sin problemas.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(JSON())


class Base(AsyncAttrs, DeclarativeBase):
    """
    V4 Base Model.
    All models should inherit from this class.
    Provides standard async attributes and common utilities.
    """

    pass


class TimestampedBase(Base):
    """
    Abstract base class providing created_at and updated_at timestamps.
    """

    __abstract__ = True

    def to_dict(self) -> dict:
        """Serializa todas las columnas y propiedades híbridas del modelo a un dict."""
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.ext.hybrid import hybrid_property

        result = {}
        mapper = sa_inspect(self.__class__)

        # 1. Columnas estándar
        for col in mapper.columns:
            key = col.key
            value = getattr(self, key, None)
            result[key] = self._serialize_value(value)

        # 2. Propiedades híbridas y descriptores (Crucial para Metadatos)
        for name, prop in self.__class__.__dict__.items():
            if isinstance(prop, hybrid_property) or (hasattr(prop, "__get__") and not name.startswith("_")):
                try:
                    value = getattr(self, name)
                    # No sobreescribir si ya existe en columnas (a menos que sea None)
                    if name not in result or result[name] is None:
                        result[name] = self._serialize_value(value)
                except Exception:
                    continue

        return result

    def _serialize_value(self, value):
        """Helper para serializar valores individuales."""
        if value is None:
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if hasattr(value, "hex") and hasattr(value, "bytes"):
            return str(value)
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        return value

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        server_default=func.now(),
        doc="The timestamp when the record was created.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        server_default=func.now(),
        server_onupdate=func.now(),
        doc="The timestamp when the record was last updated.",
    )
