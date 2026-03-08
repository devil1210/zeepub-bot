from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.library import Base


class DownloadHistory(Base):
    """
    Registro histórico de descargas de usuarios para analítica y contador de descargas.
    """

    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True)

    # Relaciones
    # Relaciones principales (v4 usa hashes como IDs)
    book_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("books.id"), index=True)
    series_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("series.id"), index=True)

    # Alias para compatibilidad legacy (apuntan a los mismos IDs/hashes)
    @hybrid_property
    def book_hash(self) -> str | None:
        return self.book_id

    @hybrid_property
    def series_hash(self) -> str | None:
        return self.series_id

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    downloaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="download_history")
