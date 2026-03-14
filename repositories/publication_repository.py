from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import and_, select
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

    def __init__(self, db_manager=None):
        super().__init__(PublicationQueue, db_manager)

    async def get_by_id(self, id: int) -> PublicationQueue | None:
        stmt = (
            select(PublicationQueue)
            .options(selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template))
            .where(PublicationQueue.id == id)
        )
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
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
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_full_queue(self, status: str | None = None, limit: int = 50) -> Sequence[PublicationQueue]:
        stmt = select(PublicationQueue).options(
            selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template)
        )
        if status:
            stmt = stmt.where(PublicationQueue.status == status)

        stmt = stmt.order_by(PublicationQueue.scheduled_for.desc()).limit(limit)
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().all()


class PublicationChannelRepository(BaseRepository[PublicationChannel]):
    """
    CRUD for Publication Channels.
    """

    def __init__(self, db_manager=None):
        super().__init__(PublicationChannel, db_manager)

    async def get_channels(self, active_only: bool = True) -> Sequence[PublicationChannel]:
        stmt = select(PublicationChannel)
        if active_only:
            stmt = stmt.where(PublicationChannel.is_active.is_(True))
        stmt = stmt.order_by(PublicationChannel.name.asc())
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().all()


class PublicationTemplateRepository(BaseRepository[PublicationTemplate]):
    """
    CRUD for Publication Templates.
    """

    def __init__(self, db_manager=None):
        super().__init__(PublicationTemplate, db_manager)

    async def get_templates(self, platform: str | None = None) -> Sequence[PublicationTemplate]:
        stmt = select(PublicationTemplate)
        if platform:
            stmt = stmt.where(PublicationTemplate.platform == platform)
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_default_template(self, platform: str) -> PublicationTemplate | None:
        stmt = select(PublicationTemplate).where(
            and_(PublicationTemplate.platform == platform, PublicationTemplate.is_default.is_(True))
        )
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


class PublicationRepository(BaseRepository[None]):
    """
    Unified Repository for Publications (Queue, Channels, Templates, Discovered Chats).
    Replaces the V3 compatibility adapter with a proper V4 implementation.
    """

    def __init__(self, db_manager=None):
        super().__init__(None, db_manager)
        self.queue = PublicationQueueRepository(db_manager)
        self.channels = PublicationChannelRepository(db_manager)
        self.templates = PublicationTemplateRepository(db_manager)

    # --- Publication Queue Methods ---
    async def get_pending_queue(self, limit: int = 50, lookahead_seconds: int = 10):
        return await self.queue.get_pending_queue(limit=limit, lookahead_seconds=lookahead_seconds)

    async def get_full_queue(self, status: str | None = None, limit: int = 50):
        return await self.queue.get_full_queue(status=status, limit=limit)

    # --- Template Methods ---
    async def get_template_by_id(self, template_id: int) -> PublicationTemplate | None:
        return await self.templates.get_by_id(template_id)

    async def get_default_template(self, platform: str) -> PublicationTemplate | None:
        return await self.templates.get_default_template(platform)

    async def get_templates(self, platform: str | None = None):
        return await self.templates.get_templates(platform)

    async def create_template(self, template: PublicationTemplate) -> PublicationTemplate:
        return await self.templates.create(template)

    async def delete_template(self, template_id: int) -> bool:
        return await self.templates.delete(template_id)

    # --- Channel Methods ---
    async def get_channels(self, active_only: bool = True):
        return await self.channels.get_channels(active_only=active_only)

    async def get_channel_by_id(self, channel_id: int) -> PublicationChannel | None:
        return await self.channels.get_by_id(channel_id)

    async def update_channel(self, channel_id: int, data: dict) -> bool:
        async with self.db_manager.get_session() as session:
            ch = await session.get(PublicationChannel, channel_id)
            if not ch:
                return False
            for k, v in data.items():
                setattr(ch, k, v)
            await session.commit()
            return True

    async def create_channel(self, channel: PublicationChannel) -> PublicationChannel:
        return await self.channels.create(channel)

    # --- Discovered Chat Methods ---
    async def get_discovered_chats(self, limit: int = 50):
        stmt = select(DiscoveredChat).order_by(DiscoveredChat.last_seen_at.desc()).limit(limit)
        async with self.db_manager.get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().all()

    async def save_discovered_chat(
        self, chat_id: Any, title: str, chat_type: str, username: str = None, member_count: int = 0
    ):
        async with self.db_manager.get_session() as session:
            chat_id_str = str(chat_id)
            stmt = select(DiscoveredChat).where(DiscoveredChat.chat_id == chat_id_str)
            result = await session.execute(stmt)
            chat = result.scalar_one_or_none()

            if not chat:
                chat = DiscoveredChat(
                    chat_id=chat_id_str,
                    title=title,
                    type=chat_type,
                    username=username,
                    member_count=member_count,
                    last_seen_at=datetime.utcnow(),
                )
                session.add(chat)
            else:
                chat.title = title
                chat.type = chat_type
                chat.username = username
                chat.member_count = member_count
                chat.last_seen_at = datetime.utcnow()

            await session.commit()
            await session.refresh(chat)
            return chat

    # --- Generic Methods (for compatibility with existing calls) ---
    async def create(self, entity: Any) -> Any:
        async with self.db_manager.get_session() as session:
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Any) -> Any:
        async with self.db_manager.get_session() as session:
            merged = await session.merge(entity)
            await session.commit()
            await session.refresh(merged)
            return merged


# Singleton instances for compatibility
pub_repo = PublicationRepository()
