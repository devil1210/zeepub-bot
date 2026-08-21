from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DownloadHistory(Base):
    __tablename__ = "download_history"
    __table_args__ = {"extend_existing": True}

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
    reason: Mapped[str | None] = mapped_column(String(255))
