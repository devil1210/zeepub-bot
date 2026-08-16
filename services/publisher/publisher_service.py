import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.communications import (
    PublicationQueue,
)
from repositories.book_repository import BookRepository
from repositories.publication_repository import PublicationRepository
from services.publisher.base import PublisherProvider
from services.publisher.facebook_provider import FacebookPublisherProvider
from services.publisher.telegram_provider import TelegramPublisherProvider
from services.publisher.twitter_provider import TwitterPublisherProvider
from utils.http_client import fetch_bytes
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)

# Re-exportar clases para mantener 100% de compatibilidad en imports de todo el proyecto
BasePublisherProvider = PublisherProvider
__all__ = [
    "PublisherProvider",
    "BasePublisherProvider",
    "TelegramPublisherProvider",
    "FacebookPublisherProvider",
    "TwitterPublisherProvider",
    "PublisherService",
    "PublisherServiceWrapper",
    "publisher_service",
]


class PublisherService:
    """
    Servicio Central de Publicación v4.0.
    Maneja la lógica de negocio, colas y orquestación de proveedores.
    """

    _queue_lock = asyncio.Lock()

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PublicationRepository(session)
        self.book_repo = BookRepository(session)  # Inyectar sesión a BookRepository
        self.providers = {
            "telegram": TelegramPublisherProvider(),
            "facebook": FacebookPublisherProvider(),
            "twitter": TwitterPublisherProvider(),
            "x": TwitterPublisherProvider(),
        }

    async def schedule_publication(
        self,
        book_hash: str,
        channel_id: int,
        scheduled_for: datetime,
        template_id: int | None = None,
        payload: dict | None = None,
    ) -> PublicationQueue:
        """Programa una nueva publicación."""
        new_item = PublicationQueue(
            book_hash=book_hash,
            channel_id=channel_id,
            template_id=template_id,
            scheduled_for=scheduled_for,
            status="pending",
            payload=payload or {},
        )
        self.session.add(new_item)
        await self.session.flush()
        return new_item

    async def process_queue(self):
        """Procesa items pendientes en la cola."""
        async with PublisherService._queue_lock:
            pending = await self.repo.get_pending_queue(limit=10)
            for item in pending:
                try:
                    item.status = "publishing"
                    await self.session.commit()

                    # Datos del libro: cargar siempre desde la base de datos si existe book_hash,
                    # y luego permitir que el payload (opcional) sobrescriba cualquier campo.
                    book_data = {}
                    if item.book_hash:
                        book = await self.book_repo.get_by_hash(item.book_hash)
                        if book:
                            english_t = (
                                getattr(book.series, "series_english", None)
                                if book.series
                                else None
                            ) or getattr(book, "series_english", None) or getattr(book, "english_title", None) or ""
                            spanish_t = (
                                getattr(book.series, "series_spanish", None)
                                if book.series
                                else None
                            ) or getattr(book, "series_spanish", None) or getattr(book, "spanish_title", None) or book.title or ""
                            romaji_t = (
                                getattr(book.series, "romaji", None)
                                or getattr(book.series, "name", None)
                                if book.series
                                else None
                            ) or getattr(book, "romaji", None) or getattr(book, "romaji_title", None) or ""
                            s_slug = (
                                getattr(book.series, "slug", None)
                                if book.series
                                else None
                            ) or getattr(book, "slug", None) or ""

                            book_data = {
                                "title": book.title,
                                "english_title": english_t,
                                "spanish_title": spanish_t,
                                "romaji_title": romaji_t,
                                "romaji": romaji_t,
                                "slug": s_slug,
                                "author": book.author
                                or (book.series.author if book.series else ""),
                                "volume": book.volume,
                                "cover_original": book.cover_original,
                                "cover_high": book.cover_high,
                                "cover_medium": book.cover_medium,
                                "cover_low": book.cover_low,
                                "portada": book.series.cover_url
                                if book.series
                                else (book.cover_medium or book.cover_low or ""),
                                "serie": english_t or spanish_t,
                                "series_english": english_t,
                                "series_spanish": spanish_t,
                                "series": (book.series.name if book.series else None)
                                or english_t
                                or spanish_t,
                                "sinopsis": (
                                    book.series.description if book.series else None
                                )
                                or book.description
                                or "",
                                "generos": book.series.tags_json
                                if book.series
                                else (book.tags_json or []),
                                "tags": book.series.tags_json
                                if book.series
                                else (book.tags_json or []),
                                "demographics": book.series.demographics_json
                                if book.series
                                else (book.demographics_json or []),
                                "demography": book.series.demographics_json
                                if book.series
                                else (book.demographics_json or []),
                                "illustrator": (
                                    book.series.illustrator if book.series else None
                                )
                                or book.illustrator
                                or "",
                                "author_jap": (
                                    book.series.author_jap if book.series else None
                                )
                                or book.author_jap
                                or "",
                                "illustrator_jap": (
                                    book.series.illustrator_jap if book.series else None
                                )
                                or book.illustrator_jap
                                or "",
                                "series_name": (
                                    book.series.name if book.series else None
                                )
                                or book.series_english
                                or "",
                                "layout_by": book.layout_by if book.layout_by else "",
                                "book_type": book.series.book_type
                                if book.series
                                else "Light Novel",
                                "publisher": book.series.publisher if book.series else "",
                                "book_hash": book.book_hash,
                                "traductor": book.translator if book.translator else "",
                                "editorial": book.publisher
                                or (book.series.publisher if book.series else ""),
                                "epub_version": book.epub_version or "",
                                "version": book.epub_version or "",
                                "modified_at_opf": book.modified_at_opf.isoformat()
                                if book.modified_at_opf
                                else "",
                                "updated_at": book.file_modified_at.isoformat()
                                if book.file_modified_at
                                else "",
                                "filename": book.filename or "",
                                "short_link": book.short_link or "",
                            }

                            # Enriquecer con metadatos y enlaces de grupo traductor, editor y maquetador por UUID de libro
                            from services.workgroup_service import workgroup_service

                            credits_meta = (
                                await workgroup_service.resolve_book_workgroup_credits(
                                    book_id=book.id,
                                    book_obj=book,
                                    raw_meta=book_data,
                                    public_link=f"https://dl.zeepubs.com/{book.short_link}" if book.short_link else None,
                                )
                            )
                            book_data.update(credits_meta)
                    if item.payload:
                        book_data.update(item.payload)

                    # Obtener proveedor
                    platform = item.channel.platform if item.channel else "telegram"
                    provider = self.providers.get(platform)

                    # Cargar plantilla personalizada si existe o buscar la predeterminada de la plataforma
                    caption = None
                    cover_quality = "high"
                    template_id_to_use = item.template_id
                    if not template_id_to_use and item.channel:
                        platform_templates = await self.repo.get_templates(platform=item.channel.platform)
                        def_tpl = next((t for t in platform_templates if t.is_default), None) or (platform_templates[0] if platform_templates else None)
                        if def_tpl:
                            template_id_to_use = def_tpl.id

                    if template_id_to_use:
                        template = await self.repo.get_template_by_id(template_id_to_use)
                        if template and template.content:
                            # Compilar plantilla con los datos del libro
                            caption = apply_publication_template(
                                template.content, book_data
                            )
                            if (
                                template.extra_config
                                and "cover_quality" in template.extra_config
                            ):
                                saved_q = template.extra_config["cover_quality"]
                                # Convertir de español (del frontend) a la clave esperada en el backend
                                cover_quality = (
                                    "high"
                                    if saved_q == "grande"
                                    else "medium"
                                    if saved_q == "mediana"
                                    else "low"
                                    if saved_q == "pequeña"
                                    else saved_q
                                )

                    if provider:
                        # Extraer message_thread_id del config del canal
                        thread_id = None
                        if item.channel and item.channel.config:
                            thread_id = item.channel.config.get("message_thread_id")

                        item_payload = item.payload if isinstance(item.payload, dict) else {}

                        success = await provider.announce_book(
                            item.channel.target_id,
                            book_data,
                            options={
                                "template_id": template_id_to_use,
                                "caption": caption,
                                "cover_quality": cover_quality,
                                "message_thread_id": thread_id,
                                "fb_album_id": item_payload.get("fb_album_id"),
                            },
                        )
                        item.status = "sent" if success else "failed"
                    else:
                        item.status = "failed"
                        item.error_message = f"Provider {platform} not found"

                    item.published_at = datetime.utcnow()
                    await self.session.commit()
                except Exception as e:
                    logger.error(f"Error procesando publicación {item.id}: {e}")
                    item.status = "failed"
                    item.error_message = str(e)
                    await self.session.commit()

    async def get_channels_with_discovery(
        self, active_only: bool = True
    ) -> dict[str, list]:
        """Obtiene la lista de canales registrados y los chats descubiertos."""
        channels = await self.repo.get_channels(active_only=active_only)
        discovered = await self.repo.get_discovered_chats()

        return {
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "target_id": c.target_id,
                    "platform": c.platform,
                    "is_active": c.is_active,
                    "is_favorite": c.is_favorite,
                    "config": c.config or {},
                }
                for c in channels
            ],
            "discovered": [
                {
                    "id": d.id,
                    "chat_id": d.chat_id,
                    "title": d.title,
                    "type": d.type,
                    "username": d.username,
                    "member_count": d.member_count,
                    "last_seen": d.last_seen_at.isoformat() if d.last_seen_at else None,
                }
                for d in discovered
            ],
        }

    async def toggle_favorite(self, channel_id: int) -> bool:
        """Alterna el estado favorito de un canal."""
        channel = await self.repo.get_channel_by_id(channel_id)
        if channel:
            channel.is_favorite = not channel.is_favorite
            await self.session.flush()
            return True
        return False

    async def promote_discovered_to_channel(self, chat_id: str, name: str) -> bool:
        """Convierte un chat descubierto en un canal oficial."""
        from models.communications import PublicationChannel

        # Verificar si ya existe el canal
        channels = await self.repo.get_channels(active_only=False)
        if any(c.target_id == str(chat_id) for c in channels):
            return False

        # Crear nuevo canal
        new_channel = PublicationChannel(
            name=name, target_id=str(chat_id), platform="telegram", is_active=True
        )
        self.session.add(new_channel)
        await self.session.flush()
        return True

    async def update_published_book(
        self,
        book_hash: str,
        new_caption: str | None = None,
        platforms: list[str] | None = None,
        template_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Edita y sincroniza publicaciones existentes (en Facebook, etc.)
        sin duplicar la foto ni crear un nuevo post.
        """
        results = {"success": False, "platforms": {}}
        from models.library import LocalBook
        from sqlalchemy import or_, select
        from sqlalchemy.orm import selectinload

        stmt = (
            select(LocalBook)
            .options(selectinload(LocalBook.series_info))
            .where(
                or_(
                    LocalBook.id == str(book_hash),
                    LocalBook.short_link == str(book_hash),
                    LocalBook.book_hash == str(book_hash),
                )
            )
        )
        res = await self.session.execute(stmt)
        book = res.scalar_one_or_none()
        if not book:
            logger.warning(
                f"Libro no encontrado para actualizar publicación: {book_hash}"
            )
            results["error"] = "Libro no encontrado"
            return results

        # 1. Resolver metadatos y créditos actualizados del libro por UUID
        from services.workgroup_service import workgroup_service

        series_info = getattr(book, "series_info", None)
        book_data = {
            "title": book.title,
            "volume": book.volume,
            "series": (series_info.series_name if series_info else None)
            or getattr(book, "series_english", None)
            or book.title,
            "series_spanish": (
                series_info.series_spanish if series_info else None
            )
            or getattr(book, "series_spanish", None)
            or book.title,
            "author": book.author or (book.series.author if book.series else ""),
            "description": (book.series.description if book.series else None)
            or book.description
            or "",
            "short_link": book.short_link or "",
            "download_link": f"https://dl.zeepubs.com/{book.short_link}" if book.short_link else "",
            "book_hash": book.id,
            "hash": book.id,
            "slug": (series_info.series_spanish if series_info else None) or book.title,
        }
        credits_meta = await workgroup_service.resolve_book_workgroup_credits(
            book_id=book.id, book_obj=book, raw_meta=book_data
        )
        book_data.update(credits_meta)

        # 2. Generar caption si no se especificó uno directamente
        if not new_caption:
            from utils.helpers import clean_caption_for_facebook
            from utils.template_engine import apply_publication_template

            raw_caption = ""
            if template_id:
                tpl = await self.repo.get_template_by_id(template_id)
                if tpl and tpl.content:
                    raw_caption = apply_publication_template(tpl.content, book_data)

            if not raw_caption:
                try:
                    platform_templates = await self.repo.get_templates(platform="facebook")
                    def_tpl = next((t for t in platform_templates if t.is_default), None) or (platform_templates[0] if platform_templates else None)
                    if def_tpl and def_tpl.content:
                        raw_caption = apply_publication_template(def_tpl.content, book_data)
                except Exception:
                    pass

            if not raw_caption:
                raw_caption = apply_publication_template(
                    TelegramPublisherProvider.FB_CAPTION_TEMPLATE, book_data
                )

            new_caption = clean_caption_for_facebook(raw_caption)

        target_platforms = platforms or ["facebook"]

        # 3. Sincronizar en Facebook
        if "facebook" in target_platforms:
            fb_target_post = book.fb_post_id or book.fb_photo_id
            if fb_target_post:
                fb_provider = self.providers.get("facebook")
                if fb_provider and hasattr(fb_provider, "update_post_message"):
                    fb_ok = await fb_provider.update_post_message(
                        post_id=fb_target_post,
                        new_message=new_caption,
                    )
                    results["platforms"]["facebook"] = fb_ok
                    if fb_ok:
                        results["success"] = True
                        logger.info(
                            f"✅ Publicación {fb_target_post} de Facebook actualizada con éxito para libro {book_hash}"
                        )
                else:
                    results["platforms"]["facebook"] = False
            else:
                results["platforms"]["facebook"] = False
                results["facebook_note"] = (
                    "El libro no tiene un post_id de Facebook registrado."
                )

        return results

    async def upsert_chat(self, chat_id: str, title: str, chat_type: str, **kwargs):
        """Descubrimiento de chats."""
        return await self.repo.upsert_discovered_chat(
            chat_id, title, chat_type, **kwargs
        )

    async def check_facebook_album(
        self,
        book_hash: str,
        channel_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Verifica el estado del álbum de Facebook para un libro específico por su hash o ID.
        """
        from config.config_settings import config
        from models.library import LocalBook
        from sqlalchemy import or_, select
        from sqlalchemy.orm import selectinload

        stmt = (
            select(LocalBook)
            .options(selectinload(LocalBook.series_info))
            .where(
                or_(
                    LocalBook.id == str(book_hash),
                    LocalBook.short_link == str(book_hash),
                    LocalBook.book_hash == str(book_hash),
                )
            )
        )
        res = await self.session.execute(stmt)
        book = res.scalar_one_or_none()
        if not book:
            return {
                "exists": False,
                "album_id": None,
                "album_name": None,
                "recommended_name": "Serie",
                "candidates": [],
                "error": "Libro no encontrado",
            }

        series_info = getattr(book, "series_info", None)
        series_name = (
            (series_info.series_spanish if series_info else None)
            or (series_info.series_name if series_info else None)
            or getattr(book, "series_spanish", None)
            or getattr(book, "series_english", None)
        )
        series_orig = series_info.series_name if series_info else None
        series_id = str(book.series_id) if getattr(book, "series_id", None) else None

        recommended = series_name or book.title

        raw_candidates = [series_name, series_orig, book.title]
        if series_name and ":" in series_name:
            raw_candidates.append(series_name.split(":")[0].strip())
        if series_name and " - " in series_name:
            raw_candidates.append(series_name.split(" - ")[0].strip())
        if series_name and "." in series_name:
            raw_candidates.append(series_name.split(".")[0].strip())

        candidates = []
        for c in raw_candidates:
            if c and c.strip() and c.strip() not in candidates:
                candidates.append(c.strip())

        target_page_id = None
        if channel_id:
            chan = await self.repo.get_channel_by_id(channel_id)
            if chan and chan.target_id:
                target_page_id = chan.target_id

        fb_provider = self.providers.get("facebook")
        if not fb_provider:
            fb_provider = FacebookPublisherProvider()

        return await fb_provider.check_album_exists(
            target_page_id=target_page_id,
            token=config.FACEBOOK_PAGE_ACCESS_TOKEN,
            series_name=recommended,
            series_id=series_id,
            alt_names=candidates,
        )


# --- Wrappers para compatibilidad global ---


class PublisherServiceWrapper:
    """Wrapper estático para PublisherService que gestiona sus propias sesiones."""

    @classmethod
    async def get_channels_with_discovery(cls, active_only: bool = True) -> dict:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            return await service.get_channels_with_discovery(active_only)

    @classmethod
    async def toggle_favorite(cls, channel_id: int) -> bool:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            res = await service.toggle_favorite(channel_id)
            await session.commit()
            return res

    @classmethod
    async def promote_discovered_to_channel(cls, chat_id: str, name: str) -> bool:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            res = await service.promote_discovered_to_channel(chat_id, name)
            await session.commit()
            return res

    @classmethod
    async def schedule_publication(cls, **kwargs) -> Any:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            res = await service.schedule_publication(**kwargs)
            await session.commit()
            return res

    @classmethod
    async def process_queue(cls):
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            await service.process_queue()

    @classmethod
    async def update_published_book(
        cls,
        book_hash: str,
        new_caption: str | None = None,
        platforms: list[str] | None = None,
        template_id: int | None = None,
    ) -> dict[str, Any]:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            return await service.update_published_book(
                book_hash=book_hash,
                new_caption=new_caption,
                platforms=platforms,
                template_id=template_id,
            )

    @classmethod
    async def check_facebook_album(
        cls,
        book_hash: str,
        channel_id: int | None = None,
    ) -> dict[str, Any]:
        from core.db_manager_pg import pg_manager

        async with pg_manager.get_session() as session:
            service = PublisherService(session)
            return await service.check_facebook_album(
                book_hash=book_hash,
                channel_id=channel_id,
            )


# Instancia exportada para compatibilidad con handlers v3.x
publisher_service = PublisherServiceWrapper
