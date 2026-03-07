from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

# Use the same Base as library_models if possible,
# but for a new file we can define it or import it.
# Usually, it's better to have a shared Base.
from models.library import Base


class DownloadHistory(Base):
    """
    Registro histórico de descargas de usuarios para analítica y contador de descargas.
    """

    __tablename__ = "download_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)

    # Relaciones
    user = relationship("User", backref="download_history")
    book_hash = Column(String(64), ForeignKey("local_books.book_hash"), index=True)
    series_hash = Column(String(64), ForeignKey("series_metadata.series_hash"), index=True)

    title = Column(String(512), nullable=False)
    downloaded_at = Column(DateTime, default=datetime.utcnow)
