from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from models.publication_models import (
    DiscoveredChat,
    PublicationChannel,
    PublicationQueue,
    PublicationTemplate,
)
from repositories.base_repository import BaseRepository


class PublicationQueueRepository(BaseRepository[PublicationQueue]):
    """
    V4 Repository for Publication Queue.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(PublicationQueue, session=session, db_manager=db_manager)

    async def get_pending_queue(self, limit: int = 50, lookahead_seconds: int = 60) -> Sequence[PublicationQueue]:
        """Obtiene ítems pendientes de publicación con margen de tiempo."""
        from datetime import timedelta

        now_plus_lookahead = datetime.utcnow() + timedelta(seconds=lookahead_seconds)
        stmt = (
            select(PublicationQueue)
            .options(
                selectinload(PublicationQueue.channel),
                selectinload(PublicationQueue.template),
                selectinload(PublicationQueue.book),
            )
            .where(
                and_(
                    PublicationQueue.status == "pending",
                    PublicationQueue.scheduled_for <= now_plus_lookahead,
                )
            )
            .order_by(PublicationQueue.scheduled_for.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_book_id(self, book_id: UUID) -> Sequence[PublicationQueue]:
        """Obtiene el historial de colas para un libro específico."""
        stmt = select(PublicationQueue).where(PublicationQueue.book_id == book_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PublicationChannelRepository(BaseRepository[PublicationChannel]):
    """
    V4 Repository for Publication Channels.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(PublicationChannel, session=session, db_manager=db_manager)

    async def get_active_channels(self, platform: str | None = None) -> Sequence[PublicationChannel]:
        """Obtiene canales activos, opcionalmente filtrados por plataforma."""
        stmt = select(PublicationChannel).where(PublicationChannel.is_active.is_(True))
        if platform:
            stmt = stmt.where(PublicationChannel.platform == platform)
        stmt = stmt.order_by(PublicationChannel.name.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PublicationTemplateRepository(BaseRepository[PublicationTemplate]):
    """
    V4 Repository for Publication Templates.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(PublicationTemplate, session=session, db_manager=db_manager)

    async def get_default_template(self, platform: str) -> PublicationTemplate | None:
        """Obtiene la plantilla por defecto para una plataforma."""
        stmt = select(PublicationTemplate).where(
            and_(PublicationTemplate.platform == platform, PublicationTemplate.is_default.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class DiscoveredChatRepository(BaseRepository[DiscoveredChat]):
    """
    V4 Repository for Discovered Chats.
    """

    def __init__(self, session=None, db_manager=None):
        super().__init__(DiscoveredChat, session=session, db_manager=db_manager)

    async def get_by_chat_id(self, chat_id: str) -> DiscoveredChat | None:
        """Busca un chat descubierto por su ID de plataforma."""
        stmt = select(DiscoveredChat).where(DiscoveredChat.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
