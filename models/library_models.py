import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import TimestampedBase
from models.user_models import DownloadLog as UserDownload
from models.rating_models import UserRating
from models.translators_models import TranslatorsGroup


class MetadataProposal(TimestampedBase):
    """
    V4 Metadata Proposal Entity.
    Stores AI-generated suggestions for series/book metadata.
    """

    __tablename__ = "metadata_proposals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    series_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Proposed Changes
    proposed_title_spanish: Mapped[str | None] = mapped_column(String(512))
    proposed_description: Mapped[str | None] = mapped_column(Text)
    proposed_slug: Mapped[str | None] = mapped_column(String(100))

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'applied', 'rejected'
    ai_confidence: Mapped[float | None] = mapped_column(Numeric)

    # Metadata context
    raw_response: Mapped[dict | None] = mapped_column(JSONB, default=dict)
