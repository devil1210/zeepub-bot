from datetime import datetime

from sqlalchemy import JSON, BigInteger, Column, DateTime, Integer, String

from .base import Base


class MetadataAudit(Base):
    """
    Auditoría de cambios automáticos en metadatos para revisión manual.
    """

    __tablename__ = "metadata_audits"

    id = Column(Integer, primary_key=True)
    series_hash = Column(String(64), index=True)
    series_name = Column(String(255))

    # Campo afectado: 'tags', 'demographics', 'title', etc.
    change_type = Column(String(50))

    old_value = Column(JSON)
    new_value = Column(JSON)

    # Estado de la revisión
    status = Column(String(20), default="pending")  # pending, reviewed, dismissed

    reviewed_at = Column(DateTime)
    reviewed_by = Column(BigInteger)  # ID usuario Telegram

    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "series_hash": self.series_hash,
            "series_name": self.series_name,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "status": self.status,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
