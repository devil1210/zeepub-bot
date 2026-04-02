from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class ThemeSyncLog(Base):
    """
    Registro de sincronizaciones de temas entre local y Supabase.
    """

    __tablename__ = "theme_sync_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'initial', 'daily', 'manual'
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'supabase_to_local', 'local_to_supabase', 'bidirectional'
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'success', 'error', 'partial'

    # Estadísticas
    local_themes_before: Mapped[int] = mapped_column(default=0)
    local_themes_after: Mapped[int] = mapped_column(default=0)
    supabase_themes_before: Mapped[int] = mapped_column(default=0)
    supabase_themes_after: Mapped[int] = mapped_column(default=0)

    # Detalles
    themes_added: Mapped[int] = mapped_column(default=0)
    themes_updated: Mapped[int] = mapped_column(default=0)
    themes_deleted: Mapped[int] = mapped_column(default=0)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "sync_type": self.sync_type,
            "direction": self.direction,
            "status": self.status,
            "local_themes_before": self.local_themes_before,
            "local_themes_after": self.local_themes_after,
            "supabase_themes_before": self.supabase_themes_before,
            "supabase_themes_after": self.supabase_themes_after,
            "themes_added": self.themes_added,
            "themes_updated": self.themes_updated,
            "themes_deleted": self.themes_deleted,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
