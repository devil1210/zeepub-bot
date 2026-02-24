import logging
from datetime import datetime

from sqlalchemy import and_, delete, select, update
from sqlalchemy.orm import selectinload

from core.db_manager_pg import pg_manager
from models.publication_models import (
    DiscoveredChat,
    PublicationChannel,
    PublicationQueue,
    PublicationTemplate,
)
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class PublicationRepository(BaseRepository[PublicationQueue]):
    """
    Repositorio para la gestión de todo lo relacionado con publicaciones:
    Canales, Plantillas y Cola de Publicación.
    """

    def __init__(self, db_manager=None):
        super().__init__(db_manager or pg_manager, "publication_queue")

    # --- Publication Queue Methods ---

    async def get_by_id(self, queue_id: int) -> PublicationQueue | None:
        async with self.db_manager.get_session() as session:
            stmt = (
                select(PublicationQueue)
                .options(selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template))
                .where(PublicationQueue.id == queue_id)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create(self, item: PublicationQueue) -> PublicationQueue:
        async with self.db_manager.get_session() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def update(self, item: PublicationQueue) -> PublicationQueue:
        # Nota: BaseRepository pide 'entity', PublicationRepository usaba 'item'
        async with self.db_manager.get_session() as session:
            session.add(item)
            await session.commit()
            await session.refresh(item)
            return item

    async def delete(self, queue_id: int) -> bool:
        async with self.db_manager.get_session() as session:
            stmt = delete(PublicationQueue).where(PublicationQueue.id == queue_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_pending_queue(self, limit: int = 50, lookahead_seconds: int = 10) -> list[PublicationQueue]:
        """Obtiene las publicaciones pendientes cuya fecha de programación ya pasó o está por pasar."""
        from datetime import timedelta

        now_plus_lookahead = datetime.utcnow() + timedelta(seconds=lookahead_seconds)
        async with self.db_manager.get_session() as session:
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
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_full_queue(self, status: str | None = None, limit: int = 100) -> list[PublicationQueue]:
        """Obtiene el historial/estado de la cola."""
        async with self.db_manager.get_session() as session:
            stmt = select(PublicationQueue).options(
                selectinload(PublicationQueue.channel), selectinload(PublicationQueue.template)
            )
            if status:
                stmt = stmt.where(PublicationQueue.status == status)

            stmt = stmt.order_by(PublicationQueue.scheduled_for.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    # --- Publication Channel Methods ---

    async def get_channel_by_id(self, channel_id: int) -> PublicationChannel | None:
        """Obtiene un canal por su ID."""
        async with self.db_manager.get_session() as session:
            return await session.get(PublicationChannel, channel_id)

    async def get_channels(self, active_only: bool = True) -> list[PublicationChannel]:
        async with self.db_manager.get_session() as session:
            stmt = select(PublicationChannel)
            if active_only:
                stmt = stmt.where(PublicationChannel.is_active.is_(True))

            # Ordenar: Favoritos primero, luego alfabético
            stmt = stmt.order_by(PublicationChannel.is_favorite.desc(), PublicationChannel.name.asc())

            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_channel(self, channel: PublicationChannel) -> PublicationChannel:
        async with self.db_manager.get_session() as session:
            session.add(channel)
            await session.commit()
            await session.refresh(channel)
            return channel

    async def update_channel(self, channel_id: int, data: dict) -> bool:
        async with self.db_manager.get_session() as session:
            stmt = update(PublicationChannel).where(PublicationChannel.id == channel_id).values(**data)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def delete_channel(self, channel_id: int) -> bool:
        async with self.db_manager.get_session() as session:
            stmt = delete(PublicationChannel).where(PublicationChannel.id == channel_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # --- Publication Template Methods ---

    async def get_template_by_id(self, template_id: int) -> PublicationTemplate | None:
        """Obtiene una plantilla por su ID."""
        async with self.db_manager.get_session() as session:
            return await session.get(PublicationTemplate, template_id)

    async def get_templates(self, platform: str | None = None) -> list[PublicationTemplate]:
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError

        async with self.db_manager.get_session() as session:
            try:
                stmt = select(PublicationTemplate)
                if platform:
                    stmt = stmt.where(PublicationTemplate.platform == platform)
                result = await session.execute(stmt)
                return list(result.scalars().all())
            except ProgrammingError as e:
                # Si la columna no existe, intentamos agregarla proactivamente
                if "extra_config" in str(e).lower() and "does not exist" in str(e).lower():
                    logger.warning("Column 'extra_config' missing in publication_templates. Patching...")
                    try:
                        # Usamos el motor directamente para el DDL
                        async with self.db_manager.engine.begin() as conn:
                            await conn.execute(
                                text("ALTER TABLE publication_templates ADD COLUMN IF NOT EXISTS extra_config JSONB;")
                            )
                        logger.info("Column 'extra_config' patched successfully.")

                        # Reintentar la consulta original
                        stmt = select(PublicationTemplate)
                        if platform:
                            stmt = stmt.where(PublicationTemplate.platform == platform)
                        result = await session.execute(stmt)
                        return list(result.scalars().all())
                    except Exception as patch_err:
                        logger.error(f"Failed to auto-patch publication_templates: {patch_err}")
                        raise e from None
                raise e from None

    async def get_default_template(self, platform: str) -> PublicationTemplate | None:
        """Obtiene la plantilla por defecto para una plataforma."""
        async with self.db_manager.get_session() as session:
            stmt = select(PublicationTemplate).where(
                and_(PublicationTemplate.platform == platform, PublicationTemplate.is_default.is_(True))
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_template(self, template: PublicationTemplate) -> PublicationTemplate:
        async with self.db_manager.get_session() as session:
            session.add(template)
            await session.commit()
            await session.refresh(template)
            return template

    async def update_template(self, template_id: int, data: dict) -> bool:
        async with self.db_manager.get_session() as session:
            stmt = update(PublicationTemplate).where(PublicationTemplate.id == template_id).values(**data)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def delete_template(self, template_id: int) -> bool:
        async with self.db_manager.get_session() as session:
            # Desvincular de la cola antes de eliminar
            stmt_update = (
                update(PublicationQueue).where(PublicationQueue.template_id == template_id).values(template_id=None)
            )
            await session.execute(stmt_update)

            stmt = delete(PublicationTemplate).where(PublicationTemplate.id == template_id)
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    # --- Discovered Chats Methods ---

    async def get_discovered_chats(self, limit: int = 20) -> list[DiscoveredChat]:
        async with self.db_manager.get_session() as session:
            stmt = select(DiscoveredChat).order_by(DiscoveredChat.last_seen_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_discovered_chat(
        self,
        chat_id: str,
        title: str,
        chat_type: str,
        username: str = None,
        member_count: int = 0,
    ):
        async with self.db_manager.get_session() as session:
            # Upsert
            stmt = select(DiscoveredChat).where(DiscoveredChat.chat_id == str(chat_id))
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.title = title
                existing.type = chat_type
                existing.username = username
                if member_count > 0:
                    existing.member_count = member_count
                existing.last_seen_at = datetime.utcnow()
                session.add(existing)
            else:
                new_chat = DiscoveredChat(
                    chat_id=str(chat_id),
                    title=title,
                    type=chat_type,
                    username=username,
                    member_count=member_count,
                )
                session.add(new_chat)

            await session.commit()


# Instancia global
pub_repo = PublicationRepository()
