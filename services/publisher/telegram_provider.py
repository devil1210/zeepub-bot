import logging
import os
import re
from datetime import datetime
from typing import Any

from services.publisher.base import PublisherProvider
from utils.helpers import normalize_demography
from utils.http_client import fetch_bytes
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class TelegramPublisherProvider(PublisherProvider):
    # (Mantenemos las plantillas pero las usamos vía el engine)
    COVER_TEMPLATE = (
        "📚 {serie} ║ {romaji_title} ║ {titulo}"
        "[?volumen]\n📖 Volumen {volumen}[/?]"
        "\n#{slug}\n"
        "[?layout_by]\n🎨 <b>Maquetado por:</b> {layout_by}[/?]"
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
            t = re.sub(r"\n{3,}", "\n\n", t).strip()
            return t

        caption_raw = options.get("caption") or apply_publication_template(
            self.COVER_TEMPLATE, book_data
        )
        msg_parts = re.split(r"<hr\s*/?>|---next---|---", caption_raw)
        msg_parts = [sanitize_tg_html(p) for p in msg_parts if p.strip()]

        # 1. Foto / Portada
        cover_quality = options.get("cover_quality", "high")

        # Determinar orden de fallback según la calidad de portada solicitada
        if cover_quality == "high":
            fallback_order = [
                "cover_high",
                "cover_original",
                "cover_medium",
                "cover_low",
            ]
        elif cover_quality == "medium":
            fallback_order = [
                "cover_medium",
                "cover_low",
                "cover_high",
                "cover_original",
            ]
        elif cover_quality == "low":
            fallback_order = [
                "cover_low",
                "cover_medium",
                "cover_high",
                "cover_original",
            ]
        elif cover_quality == "original":
            fallback_order = [
                "cover_original",
                "cover_high",
                "cover_medium",
                "cover_low",
            ]
        else:
            fallback_order = [
                f"cover_{cover_quality}",
                "cover_high",
                "cover_medium",
                "cover_low",
                "cover_original",
            ]

        cover_source = None
        for key in fallback_order:
            val = book_data.get(key)
            if val:
                cover_source = val
                break

        if not cover_source:
            cover_source = book_data.get("cover") or book_data.get("portada")

        cover_data = book_data.get("cover_bytes")
        if (
            not cover_data
            and isinstance(cover_source, str)
            and cover_source.startswith("http")
        ):
            cover_data = await fetch_bytes(cover_source)
        elif not cover_data:
            cover_data = cover_source

        # Resolver portada (bytes o ruta de archivo local) de forma asíncrona
        from services.cover_service import resolve_cover_data

        resolved_cover = (
            await resolve_cover_data(cover_data)
            if isinstance(cover_data, str)
            else cover_data
        )

        # --- CONSTRUIR RENDER RICH HTML (Telegram Premium) ---
        media = None
        files = None
        if resolved_cover:
            if isinstance(resolved_cover, bytes):
                files = {"tomozaki_cover": ("cover.jpg", resolved_cover, "image/jpeg")}
            elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                try:
                    with open(resolved_cover, "rb") as f:
                        files = {
                            "tomozaki_cover": ("cover.jpg", f.read(), "image/jpeg")
                        }
                except Exception as e:
                    logger.warning(
                        f"Error al leer archivo de portada local para anuncio: {e}"
                    )

            if files:
                media = [
                    {
                        "id": "tomozaki_cover",
                        "media": {"type": "photo", "media": "attach://tomozaki_cover"},
                    }
                ]

        # Adjuntar documento EPUB dentro del Rich Message (Telegram API 10.3)
        epub_data = (
            book_data.get("epub_bytes")
            or book_data.get("filepath")
            or book_data.get("file_path")
        )
        fname = book_data.get("filename", "libro.epub")
        if epub_data:
            try:
                import io

                if not files:
                    files = {}
                if isinstance(epub_data, (bytes, bytearray)):
                    files["epub_file"] = (
                        fname,
                        io.BytesIO(epub_data),
                        "application/epub+zip",
                    )
                elif isinstance(epub_data, str) and os.path.exists(epub_data):
                    with open(epub_data, "rb") as f:
                        files["epub_file"] = (
                            fname,
                            io.BytesIO(f.read()),
                            "application/epub+zip",
                        )

                if "epub_file" in files:
                    if not media:
                        media = []
                    media.append(
                        {
                            "id": "epub_file",
                            "media": {
                                "type": "document",
                                "media": "attach://epub_file",
                            },
                        }
                    )
            except Exception as e:
                logger.warning(
                    f"Error preparando archivo epub para Rich Message: {e}"
                )

        from services.library_ui_service import build_book_rich_blocks
        from services.rich_message_service import RichMessageService

        # Si se proporcionó una plantilla personalizada (caption), usarla directamente para RichMessage
        if options and options.get("caption"):
            clean_user_caption = (
                caption_raw.replace("__ATTACH_FILE_SIGNAL__", "")
                .replace("{archivo}", "")
                .strip()
            )
            clean_user_caption = re.sub(
                r"<img\s+src=[^>]*>", "", clean_user_caption, flags=re.IGNORECASE
            ).strip()
            if any(m.get("id") == "tomozaki_cover" for m in (media or [])):
                html_content = (
                    f'<img src="tg://photo?id=tomozaki_cover" />\n{clean_user_caption}'
                )
            else:
                html_content = clean_user_caption
            rich_blocks = None
        else:
            html_content = None
            rich_blocks = build_book_rich_blocks(
                book_data,
                has_cover=bool(files and "tomozaki_cover" in files),
                include_download=bool(files and "epub_file" in files),
                show_nav_buttons=False,
                volume_buttons=None,
            )

        # A. Intentar enviar Rich Message unificado a través de Telegram API
        try:
            if rich_blocks:
                res = await RichMessageService.send_rich_message(
                    chat_id=target_id,
                    blocks=rich_blocks,
                    files=files if files else None,
                    message_thread_id=thread_id,
                )
            else:
                res = await RichMessageService.send_rich_message(
                    chat_id=target_id,
                    html=html_content,
                    media=media,
                    files=files if files else None,
                    message_thread_id=thread_id,
                )
            if res and res.get("ok"):
                sent_msg = res.get("result")
                tg_msg_id = None
                if isinstance(sent_msg, dict):
                    tg_msg_id = sent_msg.get("message_id")
                elif hasattr(sent_msg, "message_id"):
                    tg_msg_id = sent_msg.message_id

                # Persistir tg_message_id y tg_chat_id en Book
                book_id_val = book_data.get("id") or book_data.get("book_hash")
                if book_id_val and tg_msg_id:
                    await self._persist_book_tg_ids(
                        book_id_val, str(tg_msg_id), str(target_id)
                    )

                # B. Si el epub no se incluyó embebido, enviarlo como documento separado de respaldo
                if "epub_file" not in (files or {}):
                    epub_data = (
                        book_data.get("epub_bytes")
                        or book_data.get("filepath")
                        or book_data.get("file_path")
                    )
                    if epub_data:
                        slug = book_data.get("slug")
                        if slug:
                            final_caption = (
                                slug if slug.startswith("#") else f"#{slug}"
                            )
                        else:
                            title_en = (
                                book_data.get("english_title")
                                or book_data.get("series_english")
                                or "book"
                            )
                            clean_title = re.sub(
                                r"[^\w\s]", "", title_en
                            ).replace(" ", "_")
                            final_caption = f"#{clean_title}"

                        await send_doc_bytes(
                            self.bot,
                            target_id,
                            final_caption,
                            epub_data,
                            filename=fname,
                            parse_mode="HTML",
                            message_thread_id=thread_id,
                        )
                return True
        except Exception as e:
            logger.warning(f"Error al enviar Rich Message en announce_book: {e}")

        # Fallback tradicional si falla
        logger.info(
            "Ejecutando fallback tradicional en TelegramPublisherProvider.announce_book"
        )
        photo_sent = False
        last_sent_msg_id = None
        for part in msg_parts:
            if not part.strip():
                continue

            if "__ATTACH_FILE_SIGNAL__" in part or "{archivo}" in part:
                part = (
                    part.replace("__ATTACH_FILE_SIGNAL__", "")
                    .replace("{archivo}", "")
                    .strip()
                )
                epub_data = (
                    book_data.get("epub_bytes")
                    or book_data.get("filepath")
                    or book_data.get("file_path")
                )
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
                            if hasattr(sent_photo, "message_id"):
                                last_sent_msg_id = sent_photo.message_id
                    except Exception as e:
                        logger.warning(f"Error al enviar portada como foto: {e}")

                if not sent_photo:
                    sm = await self.bot.send_message(
                        chat_id=target_id,
                        text=part,
                        parse_mode="HTML",
                        message_thread_id=thread_id,
                    )
                    if sm and hasattr(sm, "message_id"):
                        last_sent_msg_id = sm.message_id

        book_id_val = book_data.get("id") or book_data.get("book_hash")
        if book_id_val and last_sent_msg_id:
            await self._persist_book_tg_ids(
                book_id_val, str(last_sent_msg_id), str(target_id)
            )

        return True

    async def _persist_book_tg_ids(
        self, book_hash: str, message_id: str, chat_id: str
    ) -> None:
        """Helper para guardar tg_message_id y tg_chat_id en Book."""
        try:
            from sqlalchemy import update

            from core.db_manager_pg import pg_manager
            from models.library import Book

            async with pg_manager.get_session() as session:
                await session.execute(
                    update(Book)
                    .where(Book.id == str(book_hash))
                    .values(tg_message_id=str(message_id), tg_chat_id=str(chat_id))
                )
                await session.commit()
        except Exception as e:
            logger.debug(f"No se pudo persistir tg_message_id en Book: {e}")

    async def update_post_message(
        self,
        chat_id: str | int,
        message_id: str | int,
        new_message: str,
        cover: Any = None,
    ) -> bool:
        """
        Edita el mensaje/ficha existente de una publicación en Telegram.
        Limpia señales internas de archivos (__ATTACH_FILE_SIGNAL__) y actualiza portada si corresponde.
        """
        if not chat_id or not message_id or not new_message:
            return False

        clean_message = (
            new_message.replace("__ATTACH_FILE_SIGNAL__", "")
            .replace("{archivo}", "")
            .strip()
        )

        try:
            if not self.bot:
                from api.main import bot as main_bot
                self.bot = main_bot.app.bot

            # Si se proporciona portada o ruta de portada, intentar edit_message_media
            if cover:
                from telegram import InputMediaPhoto

                from services.cover_service import resolve_cover_data
                resolved_cover = await resolve_cover_data(cover)
                if resolved_cover:
                    try:
                        if isinstance(resolved_cover, bytes):
                            media = InputMediaPhoto(media=resolved_cover, caption=clean_message, parse_mode="HTML")
                            await self.bot.edit_message_media(chat_id=chat_id, message_id=int(message_id), media=media)
                            logger.info(f"✅ Portada y caption {message_id} en Telegram ({chat_id}) actualizados.")
                            return True
                        elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                            with open(resolved_cover, "rb") as f:
                                media = InputMediaPhoto(media=f, caption=clean_message, parse_mode="HTML")
                                await self.bot.edit_message_media(chat_id=chat_id, message_id=int(message_id), media=media)
                            logger.info(f"✅ Portada y caption {message_id} en Telegram ({chat_id}) actualizados.")
                            return True
                    except Exception as e:
                        logger.debug(f"Aviso edit_message_media en Telegram: {e}")

            # Intentar edit_message_caption (para mensajes con foto existentes)
            try:
                await self.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=int(message_id),
                    caption=clean_message,
                    parse_mode="HTML",
                )
                logger.info(f"✅ Caption de publicación {message_id} en Telegram editado.")
                return True
            except Exception:
                pass

            # Fallback a edit_message_text (para mensajes de texto estándar)
            await self.bot.edit_message_text(
                chat_id=chat_id,
                message_id=int(message_id),
                text=clean_message,
                parse_mode="HTML",
            )
            logger.info(f"✅ Texto de publicación {message_id} en Telegram editado.")
            return True
        except Exception as e:
            logger.error(
                f"Error editando publicación {message_id} en Telegram ({chat_id}): {e}"
            )
            return False
