from typing import Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from models.communications import PublicationChannel, PublicationQueue, PublicationTemplate
from repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)

class PublisherService:
    """
    Servicio v4.0 para gestión de publicaciones, canales y colas.
    Integrado con SQLAlchemy 2.0 Async.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.channel_repo = BaseRepository(PublicationChannel, session)
        self.template_repo = BaseRepository(PublicationTemplate, session)
        self.queue_repo = BaseRepository(PublicationQueue, session)

    async def get_active_channels(self) -> List[PublicationChannel]:
        """Obtiene la lista de canales activos."""
        from sqlalchemy import select
        query = select(PublicationChannel).where(PublicationChannel.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def schedule_publication(self, book_id: str, channel_id: int, scheduled_for: datetime, template_id: Optional[int] = None, payload: Optional[dict] = None) -> PublicationQueue:
        """Programa una publicación en la cola."""
        return await self.queue_repo.create(
            book_id=book_id,
            channel_id=channel_id,
            template_id=template_id,
            scheduled_for=scheduled_for,
            payload=payload or {},
            status="pending"
        )

    async def get_pending_publications(self) -> List[PublicationQueue]:
        """Obtiene publicaciones pendientes que deben enviarse ya."""
        from sqlalchemy import select
        now = datetime.utcnow()
        query = select(PublicationQueue).where(
            PublicationQueue.status == "pending",
            PublicationQueue.scheduled_for <= now
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def mark_as_sent(self, queue_id: int):
        """Marca una publicación como enviada."""
        await self.queue_repo.update(queue_id, status="sent", published_at=datetime.utcnow())

    async def mark_as_failed(self, queue_id: int, error: str):
        """Registra un fallo en la publicación."""
        await self.queue_repo.update(queue_id, status="failed", error_message=error)

    async def commit_changes(self):
        await self.session.commit()
