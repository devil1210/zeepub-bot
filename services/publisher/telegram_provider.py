import logging
import os
import re
from typing import Any

from services.publisher.base import PublisherProvider
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class TelegramPublisherProvider(PublisherProvider):
    """
    Proveedor para publicación en canales y supergrupos de Telegram:
    - Soporta la plantilla unificada moderna con flags (🇬🇧 🇯🇵 🇪🇸), metadatos enriquecidos,
      y bloques expandibles de Telegram Bot API 7.2+ (<blockquote expandable>) para sinopsis y archivos.
    - Envío atómico de foto con caption enriquecido y posterior adjunto del archivo .epub.
    """

    DEFAULT_UNIFIED_TEMPLATE = (
        "[?series_english]🇬🇧 <b>{series_english}</b>\n[/?]"
        "[?romaji_title]🇯🇵 <b>{romaji_title}</b>\n[/?]"
        "[?series_spanish]🇪🇸 <b>{series_spanish}</b>\n[/?]"
        "[?!series_spanish][?!series_english]📚 <b>{serie}</b>\n[/?][/?]"
        "[?volumen]📚 <b>Volumen {volumen}</b>\n[/?]"
        "\n"
        "[?autor]👤 <b>Autor:</b> {autor}\n[/?]"
        "[?illustrator]🎨 <b>Ilustrador:</b> {illustrator}\n[/?]"
        "[?layout_by]📠 <b>Maquetador:</b> #{layout_by}\n[/?]"
        "[?tipo]📦 <b>Categoría:</b> {tipo}\n[/?]"
        "[?demography]👥 <b>Demografía:</b> {demography}\n[/?]"
        "[?genres]🎭 <b>Géneros:</b> {genres}\n[/?]"
        "[?traductor]🌐 <b>Traductor:</b> {traductor}\n[/?]"
        "[?grupo_traductor]🏢 <b>Grupo Traductor:</b> {grupo_traductor}\n[/?]"
        "[?!grupo_traductor][?editorial]🏢 <b>Grupo Traductor:</b> {editorial}\n[/?][/?]"
        "\n"
        "[?sinopsis]<blockquote expandable>📖 <b>Ver Sinopsis</b>\n\n{sinopsis}</blockquote>\n\n[/?]"
        "<blockquote expandable>📁 <b>Ver Detalles del Archivo</b>\n\n"
        "[?version]ℹ️ <b>Versión Epub:</b> {version}\n[/?]"
        "[?fecha]📅 <b>Actualizado:</b> {fecha}\n[/?]"
        "[?tamaño]📦 <b>Tamaño:</b> {tamaño}\n[/?]"
        "</blockquote>\n\n"
        "#{slug}\n"
        "{archivo}"
    )
    COVER_TEMPLATE = DEFAULT_UNIFIED_TEMPLATE
    SYNOPSIS_TEMPLATE = "[?sinopsis]<blockquote expandable>📖 <b>Ver Sinopsis</b>\n\n{sinopsis}</blockquote>\n\n#{slug}[/?]"
    INFO_TEMPLATE = "<blockquote expandable>📁 <b>Ver Detalles del Archivo</b>\n\nℹ️ <b>Versión Epub:</b> {version}\n📅 <b>Actualizado:</b> {fecha}\n📦 <b>Tamaño:</b> {tamaño}</blockquote>\n\n#{slug}\n{archivo}"
    FULL_TEMPLATE = DEFAULT_UNIFIED_TEMPLATE

    FB_CAPTION_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}\n"
        "[?volumen]📖 Volumen {volumen}\n[/?]"
        "[?download_link]⬇️ Descarga: {download_link}\n[/?]"
        "[?fecha]📅 Actualizado: {fecha}\n[/?]"
        "[?tamaño]📦 Tamaño: {tamaño}\n[/?]"
        "[?layout_by]🎨 Maquetado por: {layout_by}\n[/?]"
        "[?tipo]🏷️ Categoría: {tipo}\n[/?]"
        "[?demography]👥 Demografía: {demography}\n[/?]"
        "[?genres]🎭 Géneros: {genres}\n[/?]"
        "[?autor]✍️ Autor: {autor}\n[/?]"
        "[?illustrator]🎨 Ilustrador: {illustrator}\n[/?]"
        "[?traductor]🌐 Traducción: {traductor}\n[/?]"
        "[?editorial]🏢 Grupo: {editorial}\n[/?]"
        "\n[?sinopsis]📝 Sinopsis:\n{sinopsis}\n[/?]"
        "\n[?slug]#{slug}[/?]"
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
            t = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", t, flags=re.DOTALL)
            t = re.sub(r"\n{3,}", "\n\n", t)
            return t.strip()

        # Determinar qué plantilla usar
        caption = options.get("caption")
        if not caption:
            # Buscar plantilla predeterminada de Telegram configurada en base de datos
            try:
                from core.db_manager_pg import pg_manager
                from models.communications import PublicationTemplate
                from sqlalchemy import select

                async with pg_manager.get_session() as session:
                    stmt = (
                        select(PublicationTemplate)
                        .where(PublicationTemplate.platform == "telegram")
                        .order_by(
                            PublicationTemplate.is_default.desc(),
                            PublicationTemplate.id.asc(),
                        )
                    )
                    res = await session.execute(stmt)
                    tpl = res.scalar_one_or_none()
                    if tpl and tpl.content:
                        caption = apply_publication_template(tpl.content, book_data)
            except Exception as e:
                logger.debug(f"Error consultando plantilla de BD para Telegram: {e}")

        if not caption:
            caption = apply_publication_template(self.DEFAULT_UNIFIED_TEMPLATE, book_data)

        # Detectar si debe enviar archivo adjunto
        has_file = (
            ("__ATTACH_FILE_SIGNAL__" in caption)
            or ("{archivo}" in caption)
            or options.get("send_file", False)
        )

        clean_caption = (
            caption.replace("__ATTACH_FILE_SIGNAL__", "")
            .replace("{archivo}", "")
            .strip()
        )
        clean_caption = sanitize_tg_html(clean_caption)

        # Manejar calidad de portada elegida
        cover_quality = options.get("cover_quality", "high")
        cover_source = None
        if cover_quality == "original":
            cover_source = book_data.get("cover_original") or book_data.get("portada")
        elif cover_quality == "high":
            cover_source = (
                book_data.get("cover_high")
                or book_data.get("cover_original")
                or book_data.get("portada")
            )
        elif cover_quality == "medium":
            cover_source = (
                book_data.get("cover_medium")
                or book_data.get("cover_high")
                or book_data.get("portada")
            )
        elif cover_quality == "low":
            cover_source = (
                book_data.get("cover_low")
                or book_data.get("cover_medium")
                or book_data.get("portada")
            )

        from services.cover_service import resolve_cover_data

        resolved_cover = (
            await resolve_cover_data(cover_source) if cover_source else None
        )

        # Dividir si hay separador explícito (---MSG_SPLIT---)
        parts = [p.strip() for p in clean_caption.split("---MSG_SPLIT---") if p.strip()]
        if not parts:
            parts = [clean_caption]

        photo_sent = False
        for part in parts:
            if not part:
                continue

            if cover_quality == "original" and resolved_cover and not photo_sent:
                photo_sent = True
                fname = f"cover_{book_data.get('slug', 'book')}.jpg"
                await send_doc_bytes(
                    self.bot,
                    target_id,
                    part,
                    resolved_cover
                    if isinstance(resolved_cover, bytes)
                    else open(resolved_cover, "rb").read()
                    if isinstance(resolved_cover, str) and os.path.exists(resolved_cover)
                    else b"",
                    filename=fname,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                sent_photo = None
                if resolved_cover and not photo_sent:
                    try:
                        sent_photo = await send_photo_bytes(
                            self.bot,
                            target_id,
                            part,
                            resolved_cover,
                            parse_mode="HTML",
                            message_thread_id=thread_id,
                        )
                        if sent_photo:
                            photo_sent = True
                    except Exception as e:
                        logger.warning(f"Error al enviar portada como foto: {e}")

                if not sent_photo:
                    await self.bot.send_message(
                        chat_id=target_id,
                        text=part,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )

        # Si la plantilla incluía {archivo}, enviar el archivo EPUB adjunto como documento
        if has_file:
            file_path = book_data.get("file_path") or book_data.get("filepath")
            file_source = None

            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_source = f.read()
            elif book_data.get("file_bytes"):
                file_source = book_data.get("file_bytes")
            elif book_data.get("download_url"):
                from utils.http_client import fetch_bytes

                file_source = await fetch_bytes(book_data["download_url"])
            elif book_data.get("short_link"):
                from utils.http_client import fetch_bytes

                file_source = await fetch_bytes(
                    f"https://dl.zeepubs.com/{book_data['short_link']}"
                )

            fname = (
                book_data.get("filename")
                or f"{book_data.get('titulo', 'libro')}.epub"
            )
            if not fname.endswith(".epub"):
                fname += ".epub"

            doc_caption = (
                f"#{book_data.get('slug', 'book')}" if book_data.get("slug") else ""
            )

            if file_source:
                await send_doc_bytes(
                    self.bot,
                    target_id,
                    doc_caption,
                    file_source,
                    filename=fname,
                    thumb_bytes=resolved_cover
                    if isinstance(resolved_cover, bytes)
                    else None,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            else:
                logger.warning(
                    f"No se pudo obtener el archivo EPUB para adjuntar a la publicación {target_id}"
                )

        return True
