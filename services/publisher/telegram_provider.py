import logging
import os
import re
from typing import Any

from services.publisher.base import PublisherProvider
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


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
    SYNOPSIS_TEMPLATE = (
        "📝 <b>Sinopsis:</b>\n\n<blockquote>{sinopsis}</blockquote>\n\n#{slug}"
    )
    INFO_TEMPLATE = "📂 <b>{titulo}</b>\nℹ️ Versión Epub: {version}\n📅 Actualizado: {fecha}\n📦 Tamaño: {tamaño}\n\n#{slug}{archivo}"
    FULL_TEMPLATE = (
        COVER_TEMPLATE + "\n<hr/>\n" + SYNOPSIS_TEMPLATE + "\n<hr/>\n" + INFO_TEMPLATE
    )

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
            caption = apply_publication_template(self.FULL_TEMPLATE, book_data)

        caption = sanitize_tg_html(caption)

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

        # Dividir si hay separador
        parts = [p.strip() for p in caption.split("---MSG_SPLIT---") if p.strip()]
        if not parts:
            parts = [caption]

        photo_sent = False
        for part in parts:
            if not part:
                continue

            # Si la parte incluye {archivo}, intentar enviar el archivo .epub real
            if "{archivo}" in part or (
                options.get("send_file") and book_data.get("file_path")
            ):
                part = part.replace("{archivo}", "").strip()
                file_path = book_data.get("file_path")
                file_source = None

                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        file_source = f.read()
                elif book_data.get("file_bytes"):
                    file_source = book_data.get("file_bytes")
                elif book_data.get("download_url"):
                    from utils.http_client import fetch_bytes

                    file_source = await fetch_bytes(book_data["download_url"])

                fname = book_data.get("filename") or f"{book_data.get('titulo')}.epub"
                if not fname.endswith(".epub"):
                    fname += ".epub"

                if file_source:
                    await send_doc_bytes(
                        self.bot,
                        target_id,
                        part,
                        file_source,
                        filename=fname,
                        thumb_bytes=resolved_cover
                        if isinstance(resolved_cover, bytes)
                        else None,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
                else:
                    await self.bot.send_message(
                        chat_id=target_id,
                        text=part,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
            elif cover_quality == "original" and resolved_cover and not photo_sent:
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

        return True
