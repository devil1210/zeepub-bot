from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ThemeSyncLog(Base):
    """
    Registro de sincronizaciones de temas entre local y Supabase.
    """
    __tablename__ = 'theme_sync_logs'
    
    id = Column(Integer, primary_key=True)
    sync_type = Column(String(20), nullable=False)  # 'initial', 'daily', 'manual'
    direction = Column(String(20), nullable=False)  # 'supabase_to_local', 'local_to_supabase', 'bidirectional'
    status = Column(String(20), nullable=False)  # 'success', 'error', 'partial'
    
    # Estadísticas
    local_themes_before = Column(Integer, default=0)
    local_themes_after = Column(Integer, default=0)
    supabase_themes_before = Column(Integer, default=0)
    supabase_themes_after = Column(Integer, default=0)
    
    # Detalles
    themes_added = Column(Integer, default=0)
    themes_updated = Column(Integer, default=0)
    themes_deleted = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sync_type': self.sync_type,
            'direction': self.direction,
            'status': self.status,
            'local_themes_before': self.local_themes_before,
            'local_themes_after': self.local_themes_after,
            'supabase_themes_before': self.supabase_themes_before,
            'supabase_themes_after': self.supabase_themes_after,
            'themes_added': self.themes_added,
            'themes_updated': self.themes_updated,
            'themes_deleted': self.themes_deleted,
            'errors': self.errors,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
