from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class PublicationChannel(Base):
    """
    Canales o destinos de publicación (Telegram Channels, Facebook Groups, etc.)
    """

    __tablename__ = "publication_channels"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    platform = Column(String(20), nullable=False)  # 'telegram', 'facebook'
    target_id = Column(String(100), nullable=False)  # '@ZeePubs' o ID numérico
    is_active = Column(Boolean, default=True)
    config = Column(JSON)  # Configuración extra (thread_id, tokens específicos, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación con la cola
    queued_items = relationship("PublicationQueue", back_populates="channel")


class PublicationTemplate(Base):
    """
    Plantillas de texto para las publicaciones.
    """

    __tablename__ = "publication_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)  # El template con placeholders {titulo}, {autor}, etc.
    platform = Column(String(20), nullable=False)  # 'telegram', 'facebook'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación con la cola
    queued_items = relationship("PublicationQueue", back_populates="template")


class PublicationQueue(Base):
    """
    Cola de publicaciones programadas o enviadas.
    """

    __tablename__ = "publication_queue"

    id = Column(Integer, primary_key=True)
    book_hash = Column(String(64), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("publication_channels.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("publication_templates.id"), nullable=True)

    scheduled_for = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)  # pending, publishing, sent, failed

    published_at = Column(DateTime)
    error_message = Column(Text)

    # Metadata snapshot para evitar lecturas costosas si el libro cambia
    payload = Column(JSON)  # Datos específicos que se enviarán

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    channel = relationship("PublicationChannel", back_populates="queued_items")
    template = relationship("PublicationTemplate", back_populates="queued_items")
