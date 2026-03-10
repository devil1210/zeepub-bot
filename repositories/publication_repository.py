from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.publication_models import (
    PublicationChannel,
    PublicationQueue,
    PublicationTemplate,
)

from .base_repository import BaseRepository


class PublicationQueueRepository(BaseRepository[PublicationQueue]):
    """
    CRUD for Publication Queue.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(PublicationQueue, session)

    async def get_by_id(self, id: int) -> PublicationQueue | None:
        stmt = (
            select(PublicationQueue)
            .options(selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template))
            .where(PublicationQueue.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_queue(self, limit: int = 50, lookahead_seconds: int = 10) -> Sequence[PublicationQueue]:
        from datetime import timedelta

        now_plus_lookahead = datetime.utcnow() + timedelta(seconds=lookahead_seconds)
        stmt = (
            select(PublicationQueue)
            .options(selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template))
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


class PublicationChannelRepository(BaseRepository[PublicationChannel]):
    """
    CRUD for Publication Channels.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(PublicationChannel, session)

    async def get_channels(self, active_only: bool = True) -> Sequence[PublicationChannel]:
        stmt = select(PublicationChannel)
        if active_only:
            stmt = stmt.where(PublicationChannel.is_active.is_(True))
        stmt = stmt.order_by(PublicationChannel.name.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PublicationTemplateRepository(BaseRepository[PublicationTemplate]):
    """
    CRUD for Publication Templates.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(PublicationTemplate, session)

    async def get_templates(self, platform: str | None = None) -> Sequence[PublicationTemplate]:
        stmt = select(PublicationTemplate)
        if platform:
            stmt = stmt.where(PublicationTemplate.platform == platform)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_default_template(self, platform: str) -> PublicationTemplate | None:
        stmt = select(PublicationTemplate).where(
            and_(PublicationTemplate.platform == platform, PublicationTemplate.is_default.is_(True))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
