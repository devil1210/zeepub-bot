"""
services/v4/publisher_service.py
----------------------------------
PublisherService: orquesta el flujo completo de publicación de EPUBs.

Responsabilidades:
  1. Encolar un libro para publicación en uno o varios canales
  2. Procesar la cola pendiente (llamado por un scheduler/tarea en background)
  3. Renderizar el template con datos reales del libro
  4. Despachar el mensaje al canal Telegram correspondiente
  5. Actualizar el estado del item de la cola (sent / failed)

Diseño deliberado:
  - El `bot` (Application de PTB) se recibe como parámetro en los métodos
    de despacho — el servicio NO lo almacena para evitar acoplamiento global.
  - Los errores son capturados por item, no colapsan toda la cola.
  - El renderizado de templates usa str.format_map() con un dict de contexto
    construido dinámicamente desde el modelo de libro.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from repositories.library_repository import BookRepository, SeriesRepository
from repositories.publication_repository import (
    PublicationChannelRepository,
    PublicationQueueRepository,
)

from .base_service import BaseService

if TYPE_CHECKING:
    from telegram.ext import Application


# ─────────────────────────────────────────────────────────────────────────────
# DTOs
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class EnqueueResult:
    """Resultado de encolar un libro para publicar."""

    success: bool
    queue_ids: list[int] = field(default_factory=list)
    reason: str | None = None


@dataclass
class PublishResult:
    """Resultado del procesamiento de un item de la cola."""

    queue_id: int
    success: bool
    channel_name: str = ""
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Servicio
# ─────────────────────────────────────────────────────────────────────────────

# Template por defecto para Telegram si no hay uno configurado en BD
_DEFAULT_TELEGRAM_TEMPLATE = (
    "📚 <b>{series_name}</b>\n"
    "🔖 <i>{title}</i>\n\n"
    "{description}\n\n"
    "📂 <b>Tipo:</b> {book_type}\n"
    "✍️ <b>Autor:</b> {author}\n"
    "📖 <b>Volumen:</b> {volume}\n\n"
    "#ZeePub #{slug}"
)


class PublisherService(BaseService):
    """
    Orquesta el flujo completo de publicación: encolar → procesar → despachar.
    """

    # ------------------------------------------------------------------ #
    #  Encolar                                                             #
    # ------------------------------------------------------------------ #

    async def enqueue_book(
        self,
        book_hash: str,
        channel_ids: list[int] | None = None,
        scheduled_for: datetime | None = None,
        template_id: int | None = None,
    ) -> EnqueueResult:
        """
        Añade un libro a la cola de publicación para uno o más canales.
        Si channel_ids es None, usa todos los canales activos.
        Si scheduled_for es None, programa para ahora + 30 segundos.
        """
        from models.publication_models import PublicationQueue

        scheduled_for = scheduled_for or (datetime.now(UTC) + timedelta(seconds=30))

        async with self.db.get_session() as session:
            # Obtener libro + serie para el snapshot del payload
            book_repo = BookRepository(session)
            book = await book_repo.get_by_hash(book_hash)
            if not book:
                return EnqueueResult(success=False, reason="book_not_found")

            series_repo = SeriesRepository(session)
            series = None
            if book.series_id:
                series = await series_repo.get_by_id(book.series_id)

            payload = self._build_payload(book, series)

            # Resolver canales
            channel_repo = PublicationChannelRepository(session)
            if channel_ids:
                channels = [await channel_repo.get_by_id(cid) for cid in channel_ids]
                channels = [c for c in channels if c and c.is_active]
            else:
                channels = list(await channel_repo.get_channels(active_only=True))

            if not channels:
                return EnqueueResult(success=False, reason="no_active_channels")

            queue_repo = PublicationQueueRepository(session)
            queue_ids: list[int] = []

            for channel in channels:
                item = PublicationQueue(
                    book_hash=book_hash,
                    channel_id=channel.id,
                    template_id=template_id,
                    scheduled_for=scheduled_for,
                    status="pending",
                    payload=payload,
                )
                created = await queue_repo.create(item)
                queue_ids.append(created.id)
                self.logger.info(
                    f"[ENQUEUE] book={book_hash} → canal={channel.name} scheduled={scheduled_for.isoformat()}"
                )

            return EnqueueResult(success=True, queue_ids=queue_ids)

    # ------------------------------------------------------------------ #
    #  Procesar la cola                                                    #
    # ------------------------------------------------------------------ #

    async def process_pending_queue(self, bot_app: Application) -> list[PublishResult]:
        """
        Procesa todos los items pendientes cuyo scheduled_for <= ahora.
        Devuelve una lista de PublishResult.
        Llamar desde un scheduler (APScheduler / PTB JobQueue).
        """
        results: list[PublishResult] = []

        async with self.db.get_session() as session:
            queue_repo = PublicationQueueRepository(session)
            pending = await queue_repo.get_pending_queue(limit=50, lookahead_seconds=5)

            for item in pending:
                result = await self._process_item(item, bot_app, queue_repo)
                results.append(result)

        return results

    # ------------------------------------------------------------------ #
    #  Despacho individual                                                 #
    # ------------------------------------------------------------------ #

    async def _process_item(
        self,
        item_obj,
        bot_app: Application,
        queue_repo: PublicationQueueRepository,
    ) -> PublishResult:
        """Procesa un único item de la cola."""
        channel = item_obj.channel
        channel_name = channel.name if channel else str(item_obj.channel_id)

        # Marcar como "publishing" para evitar doble proceso
        item_obj.status = "publishing"
        await queue_repo.session.flush()

        try:
            text = self._render_template(item_obj)
            await self._dispatch_telegram(bot_app, channel.target_id, text, item_obj.payload)

            item_obj.status = "sent"
            item_obj.published_at = datetime.now(UTC)
            self.logger.info(f"[PUB OK] queue_id={item_obj.id} canal={channel_name}")
            return PublishResult(queue_id=item_obj.id, success=True, channel_name=channel_name)

        except Exception as e:
            err = str(e)
            item_obj.status = "failed"
            item_obj.error_message = err[:500]
            self.logger.error(f"[PUB FAIL] queue_id={item_obj.id} error={err}")
            return PublishResult(queue_id=item_obj.id, success=False, channel_name=channel_name, error=err)

    # ------------------------------------------------------------------ #
    #  Telegram dispatch                                                   #
    # ------------------------------------------------------------------ #

    async def _dispatch_telegram(
        self,
        bot_app: Application,
        target_id: str,
        text: str,
        payload: dict | None,
    ) -> None:
        """Envía el mensaje (y opcionalmente la portada) al canal Telegram."""
        cover_url: str | None = payload.get("cover_url") if payload else None

        if cover_url and cover_url.startswith(("/", "http")):
            try:
                await bot_app.bot.send_photo(
                    chat_id=target_id,
                    photo=cover_url,
                    caption=text,
                    parse_mode="HTML",
                )
                return
            except Exception:
                pass  # Si falla la foto, despachar solo texto

        await bot_app.bot.send_message(
            chat_id=target_id,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=False,
        )

    # ------------------------------------------------------------------ #
    #  Template rendering                                                  #
    # ------------------------------------------------------------------ #

    def _render_template(self, item_obj) -> str:
        """Renderiza el template del item con el payload almacenado."""
        payload = item_obj.payload or {}
        template_content = _DEFAULT_TELEGRAM_TEMPLATE

        if item_obj.template and item_obj.template.content:
            template_content = item_obj.template.content

        # str.format_map con SafeDict para evitar KeyError en templates incompletos
        try:
            return template_content.format_map(_SafeDict(payload))
        except Exception as e:
            self.logger.warning(f"Template render error: {e}. Usando fallback.")
            return f"📚 <b>{payload.get('title', 'Nuevo libro')}</b>"

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_payload(book, series) -> dict[str, Any]:
        """Construye el snapshot del payload del libro para la cola."""
        return {
            "book_hash": book.book_hash,
            "title": book.title or "",
            "volume": str(book.volume) if book.volume else "",
            "language": book.language or "es",
            "filename": book.filename or "",
            "file_size": book.file_size or 0,
            "cover_url": getattr(book, "cover_medium", None) or getattr(book, "cover_url", None) or "",
            # Serie
            "series_name": series.series_name if series else "",
            "series_hash": series.series_hash if series else "",
            "series_spanish": (series.series_spanish if series else "") or "",
            "series_english": (series.series_english if series else "") or "",
            "author": (series.author if series else "") or "Desconocido",
            "book_type": (series.book_type if series else "") or "novel",
            "description": (series.description if series else "") or "",
            "slug": (series.slug if series else "") or "",
        }

    async def get_queue_status(self) -> dict[str, int]:
        """Devuelve un resumen del estado actual de la cola."""
        from sqlalchemy import func, select

        from models.publication_models import PublicationQueue

        async with self.db.get_session() as session:
            stmt = select(
                PublicationQueue.status,
                func.count().label("total"),
            ).group_by(PublicationQueue.status)

            result = await session.execute(stmt)
            return {row.status: row.total for row in result}


class _SafeDict(dict):
    """dict que devuelve '' para keys faltantes en str.format_map()."""

    def __missing__(self, key: str) -> str:
        return f"[{key}]"
