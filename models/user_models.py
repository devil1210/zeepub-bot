from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase


class UserLevel(TimestampedBase):
    """
    V4 User Levels (Free, Premium, VIP, etc).
    """

    __tablename__ = "user_levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Features
    daily_downloads: Mapped[int] = mapped_column(Integer, default=5)
    can_download: Mapped[bool] = mapped_column(default=True)

    # Visual
    color: Mapped[str | None] = mapped_column(String(20), default="#607D8B")

    users: Mapped[list["User"]] = relationship(back_populates="level_info")


class User(TimestampedBase):
    """
    V4 User Entity.
    Strictly mapped User for Telegram interaction and Role-based access.
    """

    __tablename__ = "users"

    # Telegram ID is the PK (BigInteger to support Telegram IDs)
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)

    # Profile
    username: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str | None] = mapped_column(String(255))

    # Access and UI configuration
    level_id: Mapped[int] = mapped_column(ForeignKey("user_levels.id"), default=6, index=True)
    role: Mapped[str] = mapped_column(String(50), default="user")  # admin, mod, user

    # Flexible structured settings
    ui_settings: Mapped[dict | None] = mapped_column(JSONB, default=dict)

    # Roles / Badges from the agent ecosystem
    roles: Mapped[list | None] = mapped_column(JSONB, default=list)

    # Relationships
    level_info: Mapped["UserLevel"] = relationship(back_populates="users")
    downloads: Mapped[list["DownloadLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "telegram_id": self.telegram_id,
            "username": self.username,
            "name": self.name,
            "nickname": self.nickname,
            "role": self.role,
            "level_id": self.level_id,
        }


class DownloadLog(TimestampedBase):
    """
    V4 Download Log.
    Tracks every book download per user for rate limiting and audit.
    """

    __tablename__ = "download_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Who downloaded
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), index=True
    )

    # What was downloaded (hash for immutability)
    book_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    book_title: Mapped[str | None] = mapped_column(String(512))

    # Context
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="downloads")
