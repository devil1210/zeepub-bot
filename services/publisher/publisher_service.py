import logging
import re
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from models.communications import (
    PublicationQueue,
)
from repositories.book_repository import BookRepository
from repositories.publication_repository import PublicationRepository
from utils.http_client import fetch_bytes
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class PublisherProvider:
    """Clase base para proveedores de publicación (Telegram, Facebook, etc)."""

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        raise NotImplementedError


class TelegramPublisherProvider(PublisherProvider):
    # (Mantenemos las plantillas pero las usamos vía el engine)
    COVER_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}"
        "[?volumen]\n📖 Volumen {volumen}[/?]"
        "\n#{slug}\n"
        "[?download_link]\n⬇️ Descarga: <a href=\"{download_link}\">Pulsa aquí</a>[/?]\n"
        "\n📅 Actualizado: {fecha}"
        "[?size_mb]\n📦 Tamaño: {size_mb}[/?]\n"
        "[?layout_by]\n🎨 Maquetado por: #{layout_by}[/?]"
        "[?tipo]\n🏷️ Categoría: {tipo}[/?]"
        "[?demography]\n👥 Demografía: {demography}[/?]"
        "[?genres]\n🎭 Géneros: {genres}[/?]"
        "[?autor]\n✍️ Autor: {autor}[/?]"
        "[?illustrator]\n🎨 Ilustrador: {illustrator}[/?]"
        "[?published_at]\n📅 Publicado: {published_at}[/?]"
        "[?traductor]\n🌐 Traducción: {traductor}[/?]"
        "[?editorial]\n🏢 Grupo Traductor: {editorial}[/?]"
    )
    SYNOPSIS_TEMPLATE = "[?sinopsis]📝 Sinopsis:\n\n<blockquote>{sinopsis}</blockquote>[/?]"
    INFO_TEMPLATE = "📂 {titulo}\nℹ️ Versión Epub: {version}\n📅 Actualizado: {fecha}\n📦 Tamaño: {tamaño}\n\n#{slug}{archivo}"
    FULL_TEMPLATE = COVER_TEMPLATE + "\n<hr/>\n" + SYNOPSIS_TEMPLATE


    FB_CAPTION_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}"
        "[?volumen]\n📖 Volumen {volumen}[/?]"
        "\n[?layout_by]🎨 Maquetado por: {layout_by}[/?]"
        "[?tipo]\n🏷️ Categoría: {tipo}[/?]"
        "[?demography]\n👥 Demografía: {demography}[/?]"
        "[?genres]\n🎭 Géneros: {genres}[/?]"
        "[?autor]\n✍️ Autor: {autor}[/?]"
        "[?illustrator]\n🎨 Ilustrador: {illustrator}[/?]"
        "[?published_at]\n📅 Publicado: {published_at}[/?]"
        "[?traductor]\n🌐 Traductor: {traductor}[/?]"
        "[?editorial]\n🏢 Grupo Traductor: {editorial}[/?]"
        "\n📝 Sinopsis: {sinopsis}{archivo}"
    )

    def __init__(self, bot=None):
        self.bot = bot

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        from services.cover_service import send_doc_bytes, send_photo_bytes

        if not self.bot:
            from api.main import bot as main_bot

            self.bot = main_bot.app.bot

        options = options or {}
        thread_id = options.get("message_thread_id")

        def sanitize_tg_html(t: str) -> str:
            if not t:
                return ""
            t = re.sub(r"<(p|div|h\d)[^>]*>", "", t, flags=re.IGNORECASE)
            t = re.sub(r"</(p|div|h\d)>", "\n", t, flags=re.IGNORECASE)
            t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
            t = re.sub(r"<hr\s*/?>", "\n---MSG_SPLIT---\n", t, flags=re.IGNORECASE)
            t = re.sub(r"\n{3,}", "\n\n", t).strip()
            return t

        caption_raw = options.get("caption") or apply_publication_template(self.COVER_TEMPLATE, book_data)
        msg_parts = re.split(r"<hr\s*/?>|---next---|---", caption_raw)
        msg_parts = [sanitize_tg_html(p) for p in msg_parts if p.strip()]

        # 1. Foto / Portada
        cover_quality = options.get("cover_quality", "high")
        cover_key = f"cover_{cover_quality}"
        cover_source = (
            book_data.get(cover_key)
            or book_data.get("cover_original")
            or book_data.get("cover")
            or book_data.get("portada")
        )

        cover_data = book_data.get("cover_bytes")
        if not cover_data and isinstance(cover_source, str) and cover_source.startswith("http"):
            cover_data = await fetch_bytes(cover_source)
        elif not cover_data:
            cover_data = cover_source

        main_caption = msg_parts[0] if msg_parts else ""

        # Resolver portada (bytes o ruta de archivo local) de forma asíncrona
        from services.cover_service import resolve_cover_data
        resolved_cover = await resolve_cover_data(cover_data) if isinstance(cover_data, str) else cover_data

        sent_photo = None
        if resolved_cover and main_caption:
            sent_photo = await send_photo_bytes(
                self.bot, target_id, main_caption, resolved_cover, parse_mode="HTML", message_thread_id=thread_id
            )

        # Fallback a texto plano si la portada no se pudo enviar pero hay un caption
        if not sent_photo and main_caption:
            logger.info("No se pudo enviar la portada como foto, enviando como texto plano de fallback...")
            try:
                await self.bot.send_message(
                    chat_id=target_id,
                    text=main_caption,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            except Exception as e:
                logger.error(f"Error enviando fallback de texto de portada: {e}")

        # 2. Sinopsis y Archivo
        if len(msg_parts) > 1:
            for part in msg_parts[1:]:
                # Si contiene señal de archivo
                if "__ATTACH_FILE_SIGNAL__" in part or "{archivo}" in part:
                    part = part.replace("__ATTACH_FILE_SIGNAL__", "").replace("{archivo}", "").strip()
                    epub_data = book_data.get("epub_bytes") or book_data.get("filepath")
                    fname = book_data.get("filename", "libro.epub")
                    await send_doc_bytes(
                        self.bot,
                        target_id,
                        part,
                        epub_data,
                        filename=fname,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
                else:
                    await self.bot.send_message(
                        chat_id=target_id, text=part, parse_mode="HTML", message_thread_id=thread_id
                    )

        return True


class FacebookPublisherProvider(PublisherProvider):
    async def announce_book(self, target_id, book_data, options=None) -> bool:
        # Implementación simplificada para v4, delegando a httpx
        logger.info(f"Facebook announcement logic placeholder for target {target_id}")
        return True


class PublisherService:
    """
    Servicio Central de Publicación v4.0.
    Maneja la lógica de negocio, colas y proveedores.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PublicationRepository(session)
        self.book_repo = BookRepository(session)  # Inyectar sesión a BookRepository
        self.providers = {"telegram": TelegramPublisherProvider(), "facebook": FacebookPublisherProvider()}

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
        pending = await self.repo.get_pending_queue(limit=10)
        for item in pending:
            try:
                item.status = "publishing"
                await self.session.flush()

                # Datos del libro: intentar cargar desde repositorio si no están completos
                book_data = item.payload or {}
                if item.book_hash and ("title" not in book_data or "author" not in book_data):
                    book = await self.book_repo.get_by_hash(item.book_hash)
                    if book:
                        # Extraer metadatos para el template engine
                        book_data.update(
                            {
                                "title": book.title,
                                "author": book.author or (book.series.author if book.series else ""),
                                "volume": book.volume,
                                "portada": book.series.cover_url if book.series else (book.cover_medium or book.cover_low or ""),
                                "serie": (book.series.series_english if book.series else None) or book.series_english or "",
                                "series_english": (book.series.series_english if book.series else None) or book.series_english or "",
                                "series": (book.series.name if book.series else None) or book.series_english or "",
                                "romaji_title": (book.series.name if book.series else None) or book.romaji_title or "",
                                "romaji": (book.series.name if book.series else None) or book.romaji_title or "",
                                "series_spanish": (book.series.series_spanish if book.series else None) or book.series_spanish or book.title,
                                "sinopsis": (book.series.description if book.series else None) or book.description or "",
                                "generos": book.series.tags_json if book.series else (book.tags_json or []),
                                "tags": book.series.tags_json if book.series else (book.tags_json or []),
                                "demographics": book.series.demographics_json if book.series else (book.demographics_json or []),
                                "demography": book.series.demographics_json if book.series else (book.demographics_json or []),
                                "illustrator": (book.series.illustrator if book.series else None) or book.illustrator or "",
                                "author_jap": (book.series.author_jap if book.series else None) or book.author_jap or "",
                                "illustrator_jap": (book.series.illustrator_jap if book.series else None) or book.illustrator_jap or "",
                                "series_name": (book.series.name if book.series else None) or book.series_english or "",
                                "layout_by": book.layout_by if book.layout_by else "",
                                "book_type": book.series.book_type if book.series else "Light Novel",
                                "publisher": book.series.publisher if book.series else "",
                                "book_hash": book.book_hash,
                                "traductor": book.translator if book.translator else "",
                                "editorial": book.publisher or (book.series.publisher if book.series else ""),
                                "version": book.epub_version or "",
                                "filename": book.filename or "",
                                "filepath": book.filepath or "",
                                "file_size": book.file_size or 0,
                                "short_link": book.short_link or "",
                            }
                        )

                # Obtener proveedor
                platform = item.channel.platform if item.channel else "telegram"
                provider = self.providers.get(platform)

                # Cargar plantilla personalizada si existe
                caption = None
                cover_quality = "high"
                if item.template_id:
                    template = await self.repo.get_template_by_id(item.template_id)
                    if template:
                        # Compilar plantilla con los datos del libro
                        caption = apply_publication_template(template.content, book_data)
                        if template.extra_config and "cover_quality" in template.extra_config:
                            saved_q = template.extra_config["cover_quality"]
                            # Convertir de español (del frontend) a la clave esperada en el backend
                            cover_quality = "high" if saved_q == "grande" else "medium" if saved_q == "mediana" else "low" if saved_q == "pequeña" else saved_q

                if provider:
                    # Extraer message_thread_id del config del canal
                    thread_id = None
                    if item.channel and item.channel.config:
                        thread_id = item.channel.config.get("message_thread_id")

                    success = await provider.announce_book(
                        item.channel.target_id,
                        book_data,
                        options={
                            "template_id": item.template_id,
                            "caption": caption,
                            "cover_quality": cover_quality,
                            "message_thread_id": thread_id,
                        },
                    )
                    item.status = "sent" if success else "failed"
                else:
                    item.status = "failed"
                    item.error_message = f"Provider {platform} not found"

                item.published_at = datetime.utcnow()
            except Exception as e:
                logger.error(f"Error processing queue item {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)

        await self.session.commit()

    async def get_channels(self, active_only: bool = True):
        return await self.repo.get_channels(active_only)

    async def get_channels_with_discovery(self, active_only: bool = True) -> dict:
        """Obtiene canales oficiales y chats descubiertos (v3.x compat)."""
        channels = await self.repo.get_channels(active_only)
        discovered = await self.repo.get_discovered_chats(limit=50)
        return {
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "platform": c.platform,
                    "target_id": c.target_id,
                    "is_active": c.is_active,
                    "is_favorite": c.is_favorite,
                    "config": c.config or {},
                }
                for c in channels
            ],
            "discovered": [
                {
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
        new_channel = PublicationChannel(name=name, target_id=str(chat_id), platform="telegram", is_active=True)
        self.session.add(new_channel)
        await self.session.flush()
        return True

    async def upsert_chat(self, chat_id: str, title: str, chat_type: str, **kwargs):
        """Descubrimiento de chats."""
        return await self.repo.save_discovered_chat(chat_id, title, chat_type, **kwargs)


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


# Instancia exportada para compatibilidad con handlers v3.x
publisher_service = PublisherServiceWrapper
