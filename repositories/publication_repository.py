from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.publication_models import (
    DiscoveredChat,
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

    async def get_full_queue(self, status: str | None = None, limit: int = 50) -> Sequence[PublicationQueue]:
        stmt = select(PublicationQueue).options(
            selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template)
        )
        if status:
            stmt = stmt.where(PublicationQueue.status == status)

        stmt = stmt.order_by(PublicationQueue.scheduled_for.desc()).limit(limit)
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

    async def get_full_queue(self, status: str | None = None, limit: int = 50):
        """Obtiene la cola completa de publicaciones."""
        async with await self._session() as s:
            repo = PublicationQueueRepository(s)
            return await repo.get_full_queue(status=status, limit=limit)

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
        """Retorna los chats descubiertos."""
        async with await self._session() as s:
            stmt = select(DiscoveredChat).order_by(DiscoveredChat.last_seen_at.desc()).limit(limit)
            result = await s.execute(stmt)
            return result.scalars().all()

    async def save_discovered_chat(
        self, chat_id: Any, title: str, chat_type: str, username: str = None, member_count: int = 0
    ):
        """Guarda o actualiza un chat descubierto."""
        async with await self._session() as s:
            chat_id_str = str(chat_id)
            stmt = select(DiscoveredChat).where(DiscoveredChat.chat_id == chat_id_str)
            result = await s.execute(stmt)
            chat = result.scalar_one_or_none()

            if not chat:
                chat = DiscoveredChat(
                    chat_id=chat_id,
                    title=title,
                    type=chat_type,
                    username=username,
                    member_count=member_count,
                    last_seen_at=datetime.utcnow(),
                )
                s.add(chat)
            else:
                chat.title = title
                chat.type = chat_type
                chat.username = username
                chat.member_count = member_count
                chat.last_seen_at = datetime.utcnow()

            await s.commit()
            return chat

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

    async def get_templates(self, platform: str | None = None):
        async with await self._session() as s:
            repo = PublicationTemplateRepository(s)
            return await repo.get_templates(platform=platform)

    async def create_template(self, template: PublicationTemplate) -> PublicationTemplate:
        async with await self._session() as s:
            s.add(template)
            await s.commit()
            await s.refresh(template)
            return template

    async def delete_template(self, template_id: int) -> bool:
        async with await self._session() as s:
            repo = PublicationTemplateRepository(s)
            template = await repo.get_by_id(template_id)
            if not template:
                return False
            await s.delete(template)
            await s.commit()
            return True


# Singleton de compatibilidad — importado por services/publisher/publisher_service.py
pub_repo = _PubRepoCompat()

# Alias para compatibilidad con código que intenta instanciar la clase
PublicationRepository = _PubRepoCompat
