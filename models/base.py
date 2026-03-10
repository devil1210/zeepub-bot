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

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        doc="The timestamp when the record was created.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        server_onupdate=func.now(),
        doc="The timestamp when the record was last updated.",
    )
