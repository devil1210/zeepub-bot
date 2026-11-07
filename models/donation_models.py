# models/donation_models.py

from datetime import datetime, timezone
from typing import Any, ClassVar

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class DonationTransaction(Base):
    """
    Registro histórico y de idempotencia para donaciones y suscripciones (Ko-fi u otras pasarelas).
    """

    __tablename__ = "donation_transactions"
    __table_args__: ClassVar[dict[str, Any]] = {"extend_existing": True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(50), default="kofi", index=True)
    message_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    kofi_transaction_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    payment_type: Mapped[str] = mapped_column(
        String(50)
    )  # Donation, Subscription, Commission, Shop Order
    amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    from_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    tier_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    is_first_subscription: Mapped[bool] = mapped_column(Boolean, default=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # Datos del usuario asociado en ZeePub
    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, index=True
    )
    user_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tier_granted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Estado de procesamiento: processed, unlinked, error, ignored
    status: Mapped[str] = mapped_column(String(50), default="processed", index=True)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
