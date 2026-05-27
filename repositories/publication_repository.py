import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.communications import (
    DiscoveredChat,
    PublicationChannel,
    PublicationQueue,
    PublicationTemplate,
)
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PublicationRepository(BaseRepository[PublicationQueue]):
    """
    Repositorio v4.0 para la gestión de publicaciones, canales y plantillas.
    """

    def __init__(self, session: AsyncSession = None):
        super().__init__(PublicationQueue, session)

    async def save_discovered_chat(
        self,
        chat_id: str,
        title: str,
        chat_type: str,
        username: str = None,
        member_count: int = 0,
    ) -> DiscoveredChat:
        """Guarda o actualiza un chat descubierto. Gestiona su propia sesión si no hay una activa."""
        from core.db_manager_pg import pg_manager

        if self.session:
            return await self._save_chat_logic(chat_id, title, chat_type, username, member_count)
        else:
            async with pg_manager.get_session() as session:
                self.session = session
                res = await self._save_chat_logic(chat_id, title, chat_type, username, member_count)
                await session.commit()
                self.session = None
                return res

    async def _save_chat_logic(self, chat_id, title, chat_type, username, member_count):
        stmt = select(DiscoveredChat).where(DiscoveredChat.chat_id == str(chat_id))
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.title = title
            existing.type = chat_type
            existing.username = username
            if member_count > 0:
                existing.member_count = member_count
            existing.last_seen_at = datetime.utcnow()
            return existing
        else:
            new_chat = DiscoveredChat(
                chat_id=str(chat_id),
                title=title,
                type=chat_type,
                username=username,
                member_count=member_count,
            )
            self.session.add(new_chat)
            return new_chat

    # --- Publication Queue Methods ---

    async def get_with_details(self, queue_id: int) -> PublicationQueue | None:
        """Obtiene un item de la cola con relaciones cargadas."""
        stmt = (
            select(PublicationQueue)
            .options(selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template))
            .where(PublicationQueue.id == queue_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_queue(self, limit: int = 50, lookahead_seconds: int = 10) -> list[PublicationQueue]:
        """Obtiene publicaciones pendientes programadas."""
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
        return list(result.scalars().all())

    # --- Publication Channel Methods ---
 
    async def get_channel_by_id(self, channel_id: int) -> PublicationChannel | None:
        """Obtiene un canal por su ID."""
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                return await session.get(PublicationChannel, channel_id)
        return await self.session.get(PublicationChannel, channel_id)
 
    async def get_channels(self, active_only: bool = True) -> list[PublicationChannel]:
        """Lista canales registrados."""
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                return await self._get_channels_logic(session, active_only)
        return await self._get_channels_logic(self.session, active_only)

    async def _get_channels_logic(self, session, active_only: bool = True):
        stmt = select(PublicationChannel)
        if active_only:
            stmt = stmt.where(PublicationChannel.is_active.is_(True))
 
        stmt = stmt.order_by(PublicationChannel.is_favorite.desc(), PublicationChannel.name.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())
 
    # --- Publication Template Methods ---
 
    async def get_template_by_id(self, template_id: int) -> PublicationTemplate | None:
        """Obtiene una plantilla por su ID."""
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                return await session.get(PublicationTemplate, template_id)
        return await self.session.get(PublicationTemplate, template_id)
 
    async def get_templates(self, platform: str | None = None) -> list[PublicationTemplate]:
        """Lista plantillas de publicación."""
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                return await self._get_templates_logic(session, platform)
        return await self._get_templates_logic(self.session, platform)

    async def _get_templates_logic(self, session, platform: str | None = None):
        stmt = select(PublicationTemplate)
        if platform:
            stmt = stmt.where(PublicationTemplate.platform == platform)
        result = await session.execute(stmt)
        return list(result.scalars().all())
 
    # --- Discovered Chats Methods ---
 
    async def get_discovered_chats(self, limit: int = 20) -> list[DiscoveredChat]:
        """Lista chats descubiertos por el bot."""
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                return await self._get_discovered_chats_logic(session, limit)
        return await self._get_discovered_chats_logic(self.session, limit)

    async def _get_discovered_chats_logic(self, session, limit: int = 20):
        stmt = select(DiscoveredChat).order_by(DiscoveredChat.last_seen_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_full_queue(self, status: str = None, limit: int = 50) -> list[PublicationQueue]:
        """Obtiene la cola completa con filtros."""
        from core.db_manager_pg import pg_manager

        # Si no hay sesión, usar una temporal (v3.x compat)
        if not self.session:
            async with pg_manager.get_session() as session:
                return await self._get_full_queue_logic(session, status, limit)
        return await self._get_full_queue_logic(self.session, status, limit)

    async def _get_full_queue_logic(self, session, status, limit):
        stmt = select(PublicationQueue).options(
            selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template)
        )
        if status:
            stmt = stmt.where(PublicationQueue.status == status)
        stmt = stmt.order_by(PublicationQueue.scheduled_for.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # --- Channel Management ---

    async def create_channel(self, channel: PublicationChannel) -> PublicationChannel:
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                session.add(channel)
                await session.commit()
                return channel
        self.session.add(channel)
        await self.session.flush()
        return channel

    async def update_channel(self, channel_id: int, data: dict):
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                stmt = select(PublicationChannel).where(PublicationChannel.id == channel_id)
                res = await session.execute(stmt)
                channel = res.scalar_one_or_none()
                if channel:
                    for k, v in data.items():
                        setattr(channel, k, v)
                    await session.commit()
        else:
            channel = await self.session.get(PublicationChannel, channel_id)
            if channel:
                for k, v in data.items():
                    setattr(channel, k, v)
                await self.session.flush()

    async def delete_channel(self, channel_id: int):
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                channel = await session.get(PublicationChannel, channel_id)
                if channel:
                    await session.delete(channel)
                    await session.commit()
        else:
            channel = await self.session.get(PublicationChannel, channel_id)
            if channel:
                await self.session.delete(channel)
                await self.session.flush()

    # --- Template Management ---

    async def create_template(self, template: PublicationTemplate) -> PublicationTemplate:
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                session.add(template)
                await session.commit()
                await session.refresh(template)
                return template
        self.session.add(template)
        await self.session.flush()
        return template

    async def update_template(self, template_id: int, data: dict):
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                template = await session.get(PublicationTemplate, template_id)
                if template:
                    for k, v in data.items():
                        setattr(template, k, v)
                    await session.commit()
        else:
            template = await self.session.get(PublicationTemplate, template_id)
            if template:
                for k, v in data.items():
                    setattr(template, k, v)
                await self.session.flush()

    async def delete_template(self, template_id: int):
        from core.db_manager_pg import pg_manager

        if not self.session:
            async with pg_manager.get_session() as session:
                template = await session.get(PublicationTemplate, template_id)
                if template:
                    await session.delete(template)
                    await session.commit()
        else:
            template = await self.session.get(PublicationTemplate, template_id)
            if template:
                await self.session.delete(template)
                await self.session.flush()


# Singleton para compatibilidad con handlers globales
pub_repo = PublicationRepository()
