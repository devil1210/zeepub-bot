from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class LibrarySource(Base):
    __tablename__ = "library_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    path: Mapped[str] = mapped_column(String(500), unique=True)
    last_scanned: Mapped[Optional[datetime]] = mapped_column()


class DownloadHistory(Base):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), index=True)
    book_id: Mapped[str] = mapped_column(ForeignKey("books.id"), index=True)

    downloaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class LibraryArchive(Base):
    """
    Tombstones para registros eliminados físicamente.
    """

    __tablename__ = "library_archive"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20))  # series, book
    item_hash: Mapped[str] = mapped_column(String(64), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB)

    archived_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    reason: Mapped[Optional[str]] = mapped_column(String(255))
