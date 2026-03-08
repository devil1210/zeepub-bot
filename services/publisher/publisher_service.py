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
        "[?layout_by]\n🎨 <b>Maquetado por:</b> #{layout_by}[/?]"
        "[?tipo]\n🏷️ <b>Categoría:</b> {tipo}[/?]"
        "[?demography]\n👥 <b>Demografía:</b> {demography}[/?]"
        "[?genres]\n🎭 <b>Géneros:</b> {genres}[/?]"
        "[?autor]\n✍️ <b>Autor:</b> {autor}[/?]"
        "[?illustrator]\n🎨 <b>Ilustrador:</b> {illustrator}[/?]"
        "[?published_at]\n📅 <b>Publicado:</b> {published_at}[/?]"
        "[?traductor]\n🌐 <b>Traductor:</b> {traductor}[/?]"
        "[?editorial]\n🏢 <b>Grupo Traductor:</b> {editorial}[/?]"
    )
    SYNOPSIS_TEMPLATE = "📝 <b>Sinopsis:</b>\n\n<blockquote>{sinopsis}</blockquote>\n\n#{slug}"
    INFO_TEMPLATE = "📂 <b>{titulo}</b>\nℹ️ Versión Epub: {version}\n📅 Actualizado: {fecha}\n📦 Tamaño: {tamaño}\n\n#{slug}{archivo}"
    FULL_TEMPLATE = COVER_TEMPLATE + "\n<hr/>\n" + SYNOPSIS_TEMPLATE + "\n<hr/>\n" + INFO_TEMPLATE

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
            from core.bot import telegram_bot

            self.bot = telegram_bot

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
        cover_source = book_data.get(cover_key) or book_data.get("cover_original") or book_data.get("cover")

        cover_data = book_data.get("cover_bytes")
        if not cover_data and isinstance(cover_source, str) and cover_source.startswith("http"):
            cover_data = await fetch_bytes(cover_source)
        elif not cover_data:
            cover_data = cover_source

        main_caption = msg_parts[0] if msg_parts else ""
        await send_photo_bytes(
            self.bot, target_id, main_caption, cover_data, parse_mode="HTML", message_thread_id=thread_id
        )

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
                                "author": book.author,
                                "volume": book.volume,
                                "portada": book.series.cover_medium if book.series else None,
                                "series_spanish": book.series.series_spanish if book.series else book.title,
                                "sinopsis": book.series.description if book.series else "",
                                "generos": book.series.genres if book.series else [],
                                "book_hash": book.book_hash,
                            }
                        )

                # Obtener proveedor
                platform = item.channel.platform if item.channel else "telegram"
                provider = self.providers.get(platform)

                if provider:
                    success = await provider.announce_book(
                        item.channel.target_id, book_data, options={"template_id": item.template_id}
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

    async def upsert_chat(self, chat_id: str, title: str, chat_type: str, **kwargs):
        """Descubrimiento de chats."""
        return await self.repo.upsert_discovered_chat(chat_id, title, chat_type, **kwargs)
