# src/models/library.py
import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy import (
    String, Text, Integer, Boolean, Numeric, 
    BigInteger, DateTime, JSON, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from src.models.base import TimestampedBase

class SeriesMetadata(TimestampedBase):
    """Obra/Serie completa."""
    __tablename__ = "series_metadata"
    
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    title_spanish: Mapped[Optional[str]] = mapped_column(String(512))
    slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    author: Mapped[Optional[str]] = mapped_column(String(512))
    description: Mapped[Optional[str]] = mapped_column(Text)
    book_type: Mapped[str] = mapped_column(String(50), default="Light Novel")
    cover_url: Mapped[Optional[str]] = mapped_column(String(512))
    tags: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    
    books: Mapped[List["LocalBook"]] = relationship(
        back_populates="series", cascade="all, delete-orphan", lazy="selectin"
    )

class LocalBook(TimestampedBase):
    """Archivo EPUB físico."""
    __tablename__ = "local_books"
    
    hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    series_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("series_metadata.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    volume_number: Mapped[float] = mapped_column(Numeric, default=0.0)
    is_uncensored: Mapped[bool] = mapped_column(Boolean, default=False)
    color_mode: Mapped[str] = mapped_column(String(20), default="bw")
    
    series: Mapped[Optional["SeriesMetadata"]] = relationship(back_populates="books")

    @hybrid_property
    def filepath(self): return self.file_path
    @hybrid_property
    def volume(self): return float(self.volume_number)

# --- Modelos de IA y Auditoría (Rescatados de Restart) ---

class MetadataProposal(TimestampedBase):
    """Propuestas generadas por Gemini 3.1 Flash Lite."""
    __tablename__ = "metadata_proposals"
    
    series_hash: Mapped[str] = mapped_column(String(64), index=True)
    proposed_title: Mapped[Optional[str]] = mapped_column(String(512))
    proposed_description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, accepted, rejected
    confidence: Mapped[Optional[float]] = mapped_column(Numeric)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSONB)

class UploadHistory(TimestampedBase):
    """Log de subidas vía Bot o Mini App."""
    __tablename__ = "upload_history"
    
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    filename: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(20), default="success")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

# Aliases Legacy
Book = LocalBook
Series = SeriesMetadata
