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


# ─────────────────────────────────────────────────────────────────────────────
# Adaptador de compatibilidad V3 → V4
# El V3 publisher_service espera un singleton `pub_repo` con métodos de alto
# nivel que gestionan su propia sesión. Este adaptador lo provee usando
# el DBManager V4.
# ─────────────────────────────────────────────────────────────────────────────


class _PubRepoCompat:
    """
    Singleton de compatibilidad para que el V3 publisher_service pueda importar
    `pub_repo` sin cambios. Internamente abre sesiones async de forma autónoma.
    """

    def _get_engine(self):
        from sqlalchemy.ext.asyncio import create_async_engine

        from config.config_settings import config

        url = config.DATABASE_URL
        if not url:
            raise RuntimeError("DATABASE_URL no configurada")
        return create_async_engine(url, echo=False)

    async def _session(self):
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

        engine = self._get_engine()
        maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        return maker()

    async def get_pending_queue(self, limit: int = 50, lookahead_seconds: int = 10):
        async with await self._session() as s:
            repo = PublicationQueueRepository(s)
            return await repo.get_pending_queue(limit=limit, lookahead_seconds=lookahead_seconds)

    async def get_template_by_id(self, template_id: int) -> PublicationTemplate | None:
        async with await self._session() as s:
            repo = PublicationTemplateRepository(s)
            return await repo.get_by_id(template_id)

    async def get_default_template(self, platform: str) -> PublicationTemplate | None:
        async with await self._session() as s:
            repo = PublicationTemplateRepository(s)
            return await repo.get_default_template(platform)

    async def create(self, entity):
        async with await self._session() as s:
            s.add(entity)
            await s.commit()
            await s.refresh(entity)
            return entity

    async def update(self, entity):
        async with await self._session() as s:
            merged = await s.merge(entity)
            await s.commit()
            return merged

    async def get_channels(self, active_only: bool = True):
        async with await self._session() as s:
            repo = PublicationChannelRepository(s)
            return await repo.get_channels(active_only=active_only)

    async def get_discovered_chats(self, limit: int = 50):
        """
        Compatibilidad: el V3 pedía chats descubiertos.
        Retorna lista vacía si no existe la tabla (V4 no la implementa aún).
        """
        return []

    async def get_channel_by_id(self, channel_id: int) -> PublicationChannel | None:
        async with await self._session() as s:
            repo = PublicationChannelRepository(s)
            return await repo.get_by_id(channel_id)

    async def update_channel(self, channel_id: int, data: dict) -> bool:
        async with await self._session() as s:
            repo = PublicationChannelRepository(s)
            ch = await repo.get_by_id(channel_id)
            if not ch:
                return False
            for k, v in data.items():
                setattr(ch, k, v)
            await s.commit()
            return True

    async def create_channel(self, channel: PublicationChannel) -> PublicationChannel:
        async with await self._session() as s:
            s.add(channel)
            await s.commit()
            await s.refresh(channel)
            return channel


# Singleton de compatibilidad — importado por services/publisher/publisher_service.py
pub_repo = _PubRepoCompat()
