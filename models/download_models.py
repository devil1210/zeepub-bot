from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

# Use the same Base as library_models if possible,
# but for a new file we can define it or import it.
# Usually, it's better to have a shared Base.
from models.library_models import Base


class DownloadHistory(Base):
    """
    Registro histórico de descargas de usuarios para analítica y contador de descargas.
    """

    __tablename__ = "download_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    author = Column(String(255))
    download_url = Column(String(1024))
    file_size = Column(Integer)
    downloaded_at = Column(DateTime, default=datetime.utcnow)

    # Metadata adicional para tracking
    romaji_title = Column(String(512))
    series = Column(String(255))
    volume = Column(String(50))
    translator = Column(String(255))
    clean_title = Column(String(512))
    book_hash = Column(String(64), index=True)
    is_uncensored = Column(Integer, default=0)
    color_mode = Column(String(50))
