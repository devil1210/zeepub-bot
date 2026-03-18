from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


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
        """Serializa todas las columnas del modelo a un dict."""
        from sqlalchemy import inspect as sa_inspect

        result = {}
        mapper = sa_inspect(self.__class__)
        for col in mapper.columns:
            key = col.key
            value = getattr(self, key, None)
            # Convertir UUIDs y datetimes a string para serialización
            if hasattr(value, "isoformat"):
                result[key] = value.isoformat()
            elif hasattr(value, "hex") and hasattr(value, "bytes"):
                # UUID object
                result[key] = str(value)
            else:
                result[key] = value
        return result

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
