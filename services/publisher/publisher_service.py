import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class PublisherProvider(ABC):
    @abstractmethod
    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        """
        Announces a book on the platform (cover, sinopsis, info).
        """
        pass


class TelegramPublisherProvider(PublisherProvider):
    # Plantillas por defecto para facilitar edición/copia
    SYNOPSIS_TEMPLATE = "<b>Sinopsis:</b>\n<blockquote>{sinopsis}</blockquote>\n#{slug}"
    INFO_TEMPLATE = (
        "📂 <b>{titulo}</b>\n"
        "ℹ️ Versión Epub: {version}\n"
        "📅 Actualizado: {fecha}\n"
        "📦 Tamaño: {size_mb:.2f} MB{rating_txt}\n"
        "#{slug}"
    )

    # Calidad de portada por defecto: 'original', 'high', 'medium', 'low'
    COVER_QUALITY = "low"

    def __init__(self, bot=None):
        self.bot = bot

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        """
        Implementation of book announcement for Telegram.
        """
        from telegram import InlineKeyboardMarkup

        from config.config_settings import config
        from services.telegram_service import send_doc_bytes, send_photo_bytes
        from utils.helpers import (
            escapar_html,
            formatear_mensaje_portada,
            generar_slug_from_meta,
        )

        if not self.bot:
            from api.main import bot as main_bot

            self.bot = main_bot.app.bot

        options = options or {}
        thread_id = options.get("message_thread_id")

        # --- Lógica de Plantilla Multi-mensaje ---
        custom_content = options.get("caption")
        msg_parts = []
        if custom_content:
            # Separadores comunes: <hr>, ---next---, o ---
            msg_parts = re.split(r"<hr\s*/?>|---next---|---", custom_content)
            msg_parts = [p.strip() for p in msg_parts if p.strip()]

        # 1. Mensaje de Portada (o Texto Principal)
        caption = (
            msg_parts[0]
            if len(msg_parts) > 0
            else (custom_content or formatear_mensaje_portada(book_data))
        )

        # Selección de calidad de portada
        quality = options.get("cover_quality") or self.COVER_QUALITY
        cover_key = f"cover_{quality}"
        cover_path_or_url = book_data.get(cover_key) or book_data.get("cover")

        # Prioridad: Bytes directos > URL/Path
        cover_data = book_data.get("cover_bytes")
        if not cover_data and cover_path_or_url:
            if isinstance(cover_path_or_url, str) and (
                cover_path_or_url.startswith("http://") or cover_path_or_url.startswith("https://")
            ):
                from utils.http_client import fetch_bytes

                # Fetch bytes from URL
                auth = None
                if config.OPDS_AUTH:
                    import aiohttp

                    auth = aiohttp.BasicAuth(config.OPDS_AUTH[0], config.OPDS_AUTH[1])
                cover_data = await fetch_bytes(cover_path_or_url, timeout=15, auth=auth)
            else:
                cover_data = cover_path_or_url

        sent_photo = await send_photo_bytes(
            self.bot,
            target_id,
            caption,
            cover_data,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

        # Fallback: si no hay portada o falló, enviamos el texto igualmente
        if not sent_photo:
            try:
                await self._send_message(
                    chat_id=target_id,
                    text=caption,
                    parse_mode="HTML",
                    thread_id=thread_id,
                )
            except Exception as e:
                logger.error(f"Error sending novel info (text fallback): {e}")

        # 2. Sinopsis / Mensaje Intermedio
        sinopsis = ""
        if len(msg_parts) > 1:
            sinopsis = msg_parts[1]
        else:
            # Comportamiento por defecto
            raw_sinopsis = (
                book_data.get("description")
                or book_data.get("summary")
                or book_data.get("sinopsis")
            )
            if raw_sinopsis:
                sinopsis_esc = escapar_html(raw_sinopsis)
                slug = generar_slug_from_meta(book_data)
                sinopsis = self.SYNOPSIS_TEMPLATE.format(sinopsis=sinopsis_esc, slug=slug or "")
                if not slug:
                    sinopsis = sinopsis.replace("\n#", "").strip()

        if sinopsis:
            try:
                await self._send_message(
                    chat_id=target_id,
                    text=sinopsis,
                    parse_mode="HTML",
                    thread_id=thread_id,
                )
            except Exception as e:
                logger.error(f"Error sending intermediate message: {e}")

        # 3. Archivo EPUB / Mensaje Final
        info_text = ""
        if len(msg_parts) > 2:
            info_text = msg_parts[2]
        else:
            # Comportamiento por defecto
            info_text = self._format_info_text(book_data)

        epub_data = (
            book_data.get("epub_bytes") or book_data.get("epub_buffer") or book_data.get("filepath")
        )

        # Si es una publicación con archivo, no solemos querer botones de "Descargar"
        # ya que el archivo está ahí mismo. Solo usamos botones si se pasan customizados.
        keyboard = options.get("custom_keyboard")
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        if epub_data:
            from urllib.parse import unquote, urlparse

            fname = book_data.get("filename")
            if not fname and book_data.get("url"):
                fname = unquote(urlparse(book_data["url"]).path.split("/")[-1])
            if not fname:
                fname = "archivo.epub"

            try:
                sent_doc = await send_doc_bytes(
                    self.bot,
                    target_id,
                    info_text,
                    epub_data,
                    filename=fname,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                    reply_markup=reply_markup,
                )

                if "state" in options and sent_doc:
                    options["state"]["msg_info_id"] = sent_doc.message_id
                    options["state"]["msg_botones_id"] = sent_doc.message_id

            except Exception as e:
                logger.error(f"Error sending EPUB: {e}")
                # Fallback final a mensaje de texto si falla el envío del documento
                await self._send_message(
                    chat_id=target_id,
                    text=info_text,
                    parse_mode="HTML",
                    thread_id=thread_id,
                )
        else:
            # Si no hay archivo, enviamos el texto informativo solo
            await self._send_message(
                chat_id=target_id,
                text=info_text,
                parse_mode="HTML",
                thread_id=thread_id,
                reply_markup=reply_markup,
            )

        return True

    async def _send_message(
        self, chat_id, text, parse_mode=None, reply_markup=None, thread_id=None
    ):
        """Helper to send messages with thread fallback."""
        from telegram.error import BadRequest

        try:
            return await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                message_thread_id=thread_id,
            )
        except BadRequest as e:
            if "thread not found" in str(e).lower() and thread_id:
                logger.warning(
                    f"Thread {thread_id} not found in {chat_id}, falling back to main chat."
                )
                return await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    message_thread_id=None,
                )
            raise e

    def _format_info_text(self, meta: dict[str, Any]) -> str:
        from utils.helpers import generar_slug_from_meta

        version = meta.get("epub_version", "2.0")
        fecha = meta.get("fecha_modificacion", meta.get("updated_at", "Desconocida"))
        titulo = meta.get("titulo_volumen") or meta.get("title", "Desconocido")
        size_mb = meta.get("size_mb", 0.0)

        # Stars/Rating
        rating_txt = ""
        avg = meta.get("rating_average")
        count = meta.get("rating_count", 0)
        if avg and avg > 0:
            rating_txt = f"\n⭐ {avg:.1f} ({count} votos)"

        slug = generar_slug_from_meta(meta)
        info_text = self.INFO_TEMPLATE.format(
            titulo=titulo,
            version=version,
            fecha=fecha,
            size_mb=size_mb,
            rating_txt=rating_txt,
            slug=slug or "",
        )

        if not slug:
            info_text = info_text.replace("\n#", "").strip()

        return info_text


class FacebookPublisherProvider(PublisherProvider):
    def __init__(self):
        pass

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        import logging

        import httpx

        from config.config_settings import config
        from utils.helpers import (
            formatear_metadata_fb,
            formatear_titulo_fb,
            validate_facebook_credentials,
        )

        logger = logging.getLogger(__name__)

        # 1. Validate Credentials
        is_valid, error_msg = validate_facebook_credentials(config)
        if not is_valid:
            logger.error(f"Facebook credentials invalid: {error_msg}")
            return False

        # 2. Build Caption (if not provided in options)
        caption = options.get("caption")
        if not caption:
            # Generate from book_data
            # Logic replicated from send_direct / fb_preview
            # a. Title
            title_block = formatear_titulo_fb(book_data)

            # b. Generate Direct Download Link (Secure short URL)
            raw_url = (
                book_data.get("filepath") or book_data.get("download_url") or book_data.get("url")
            )
            public_link = None
            if raw_url:
                try:
                    from utils.url_cache import create_short_url

                    dl_domain = config.DL_DOMAIN.rstrip("/")
                    if not dl_domain.startswith("http"):
                        dl_domain = f"https://{dl_domain}"

                    url_hash = create_short_url(
                        raw_url,
                        book_title=book_data.get("title"),
                        series_name=book_data.get("series"),
                    )
                    public_link = f"{dl_domain}/api/dl/{url_hash}"
                except Exception as e:
                    logger.error(f"Failed to create secure link for FB: {e}")
                    # If short url fails, we DO NOT expose the raw_url if it is a local path
                    if raw_url.startswith("http"):
                        public_link = raw_url
                    else:
                        public_link = None

            link_block = f"🚀 Descarga Directa: {public_link}" if public_link else ""

            # c. Metadata
            metadata_block = formatear_metadata_fb(book_data)

            # d. Synopsis
            from utils.helpers import limpiar_html_basico

            sinopsis = book_data.get("sinopsis") or book_data.get("description")
            sinopsis_block = ""
            if sinopsis:
                # FB doesn't support blockquotes/b/i tags via API usually
                clean_syn = limpiar_html_basico(sinopsis)
                sinopsis_block = f"Sinopsis:\n{clean_syn}"

            parts = [title_block, link_block, metadata_block, sinopsis_block]
            caption = "\n\n".join(p for p in parts if p).strip()
            # Clean HTML tags that might remain in metadata formatting
            caption = re.sub(r"<.*?>", "", caption)

            # FB length limit check
            if len(caption) > 2100:
                caption = caption[:2097] + "..."

        # 3. Handle Cover (URL vs Binary)
        cover_url = book_data.get("cover_url") or book_data.get("portada")
        cover_binary = book_data.get("cover_bytes") or book_data.get("cover")

        # Fallback if cover is a local path string
        if isinstance(cover_binary, str) and not cover_binary.startswith("http"):
            if os.path.exists(cover_binary):
                with open(cover_binary, "rb") as f:
                    cover_binary = f.read()
            else:
                cover_binary = None

        # 4. Post to Graph API
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                if cover_binary and (not cover_url or not cover_url.startswith("http")):
                    # Multipart upload for binary data
                    return await self._upload_photo_binary(client, config, cover_binary, caption)

                if cover_url and cover_url.startswith("http"):
                    # URL-based upload
                    url = f"https://graph.facebook.com/{config.FACEBOOK_GROUP_ID}/photos"
                    params = {
                        "url": cover_url,
                        "caption": caption,
                        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
                    }
                    resp = await client.post(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        logger.error(f"FB URL Post Error: {resp.text}")
                        # If URL failed, try binary if available
                        if cover_binary:
                            return await self._upload_photo_binary(
                                client, config, cover_binary, caption
                            )
                        return False
                    return True

                logger.error("No valid cover source (URL or binary) for Facebook post.")
                return False

        except Exception as e:
            logger.error(f"Error publishing to Facebook: {e}")
            return False

    async def _upload_photo_binary(self, client, config, binary_data, caption):
        """Uploads a photo using multipart/form-data."""
        url = f"https://graph.facebook.com/{config.FACEBOOK_GROUP_ID}/photos"
        files = {"source": ("cover.jpg", binary_data, "image/jpeg")}
        data = {
            "caption": caption,
            "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        }
        try:
            resp = await client.post(url, data=data, files=files, timeout=60)
            if resp.status_code != 200:
                logger.error(f"FB Binary Post Error: {resp.text}")
                return False
            return True
        except Exception as e:
            logger.error(f"FB Binary Upload Exception: {e}")
            return False


class PublisherService:
    def __init__(self, default_provider: PublisherProvider = None, pub_repo=None):
        self.providers = {
            "telegram": default_provider or TelegramPublisherProvider(),
            "facebook": FacebookPublisherProvider(),
        }
        from repositories.publication_repository import pub_repo as default_repo

        self.repo = pub_repo or default_repo

    async def announce(
        self,
        platform: str,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        """Envia una publicación inmediata."""
        provider = self.providers.get(platform)
        if not provider:
            logger.error(f"Provider not found for platform: {platform}")
            return False
        return await provider.announce_book(target_id, book_data, options)

    async def schedule_publication(
        self,
        book_hash: str,
        channel_id: int,
        scheduled_for: datetime,
        template_id: int | None = None,
        payload: dict | None = None,
    ) -> Any:
        """Programa una publicación en la cola."""
        from models.publication_models import PublicationQueue

        item = PublicationQueue(
            book_hash=book_hash,
            channel_id=channel_id,
            template_id=template_id,
            scheduled_for=scheduled_for,
            status="pending",
            payload=payload,
        )
        return await self.repo.create(item)

    async def process_queue(self):
        """Procesa los ítems pendientes en la cola."""
        pending = await self.repo.get_pending_queue()
        if not pending:
            return

        logger.info(f"Procesando {len(pending)} publicaciones programadas...")

        for item in pending:
            try:
                # 1. Marcar como procesando
                item.status = "publishing"
                await self.repo.update(item)

                # 2. Obtener datos del libro si no están en payload
                book_data = item.payload
                if not book_data:
                    from repositories.book_repository import book_repo

                    book = await book_repo.get_by_hash(item.book_hash)
                    if not book:
                        raise Exception(f"Book with hash {item.book_hash} not found")
                    book_data = book.to_dict()

                # 3. Aplicar plantilla si existe
                options = {}
                if item.template:
                    options["caption"] = self._apply_template(item.template.content, book_data)
                    # Añadir configuraciones extra (calidad de portada, etc.)
                    if item.template.extra_config:
                        options.update(item.template.extra_config)

                # 4. Publicar
                success = await self.announce(
                    platform=item.channel.platform,
                    target_id=item.channel.target_id,
                    book_data=book_data,
                    options=options,
                )

                if success:
                    item.status = "sent"
                    item.published_at = datetime.utcnow()
                else:
                    item.status = "failed"
                    item.error_message = "Provider announce_book returned False"

            except Exception as e:
                logger.error(f"Error publishing queued item {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)

            await self.repo.update(item)

    def _apply_template(self, template_str: str, data: dict) -> str:
        """Aplica placeholders con todos los campos disponibles de LocalBook."""
        try:
            # Preparar mapeo de variables (snake_case y español para comodidad)
            mapping = {
                "title": data.get("title", ""),
                "titulo": data.get("title", ""),
                "author": data.get("author", "Desconocido"),
                "autor": data.get("author", "Desconocido"),
                "series": data.get("series", ""),
                "serie": data.get("series", ""),
                "volume": data.get("volume", ""),
                "volumen": data.get("volume", ""),
                "description": data.get("description", ""),
                "sinopsis": data.get("description", ""),
                "summary": data.get("summary", ""),
                "resumen": data.get("summary", ""),
                "tags": (
                    ", ".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else ""
                ),
                "etiquetas": (
                    ", ".join(data.get("tags", [])) if isinstance(data.get("tags"), list) else ""
                ),
                "genres": ", ".join(data.get("tags", []))
                if isinstance(data.get("tags"), list)
                else "",
                "language": data.get("language", "es"),
                "idioma": data.get("language", "es"),
                "publisher": data.get("publisher", ""),
                "editorial": data.get("publisher", ""),
                "translator": data.get("translator", ""),
                "traductor": data.get("translator", ""),
                "layout_by": data.get("layout_by", ""),
                "maquetador": data.get("layout_by", ""),
                "book_type": data.get("book_type", ""),
                "tipo": data.get("book_type", ""),
                "isbn": data.get("isbn", ""),
                "asin": data.get("asin", ""),
                "rating": data.get("rating_average", 0.0),
                "votes": data.get("rating_count", 0),
                "size": data.get("size", "0 MB"),
                "tamaño": data.get("size", "0 MB"),
                "version": data.get("epub_version", ""),
                "slug": data.get("slug", ""),
                "hash": data.get("book_hash", ""),
                # Portadas (URLs)
                "cover_original": data.get("cover_original", ""),
                "cover_high": data.get("cover_high", ""),
                "cover_medium": data.get("cover_medium", ""),
                "cover_low": data.get("cover_low", ""),
            }

            # Reemplazar placeholders manual para evitar errores con llaves de HTML si las hay
            # Usamos .format() pero con un fallback si falla por llaves extras
            try:
                # Filtrar solo las llaves que están en nuestro mapping para evitar KeyErrors
                placeholders = re.findall(r"\{(\w+)\}", template_str)
                safe_mapping = {p: mapping.get(p, f"{{{p}}}") for p in placeholders}
                return template_str.format(**safe_mapping)
            except Exception:
                result = template_str
                for key, val in mapping.items():
                    result = result.replace(f"{{{key}}}", str(val))
                return result
        except Exception as e:
            logger.warning(f"Error applying template: {e}")
            return template_str

    async def get_channels_with_discovery(self, active_only: bool = True) -> dict:
        """
        Devuelve canales configurados y chats descubiertos.
        """
        channels = await self.repo.get_channels(active_only=active_only)
        discovered = await self.repo.get_discovered_chats(limit=50)

        # Mapeamos a diccionarios simples
        return {
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "platform": c.platform,
                    "target_id": c.target_id,
                    "is_favorite": c.is_favorite,
                    "is_active": c.is_active,
                }
                for c in channels
            ],
            "discovered": [
                {
                    "chat_id": d.chat_id,
                    "title": d.title,
                    "type": d.type,
                    "member_count": d.member_count,
                    "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
                }
                for d in discovered
            ],
        }

    async def toggle_favorite(self, channel_id: int) -> bool:
        """Alterna el estado de favorito de un canal."""
        target = await self.repo.get_channel_by_id(channel_id)
        if target:
            new_val = not target.is_favorite
            return await self.repo.update_channel(channel_id, {"is_favorite": new_val})
        return False

    async def promote_discovered_to_channel(self, chat_id: str, name: str) -> Any:
        """Convierte un chat descubierto en un canal de publicación oficial."""
        from models.publication_models import PublicationChannel

        # Check if already exists
        channels = await self.repo.get_channels(active_only=False)
        if any(c.target_id == str(chat_id) for c in channels):
            return None

        new_channel = PublicationChannel(
            name=name,
            platform="telegram",  # Asumimos telegram por ahora
            target_id=str(chat_id),
            is_active=True,
            is_favorite=True,  # Promovidos suelen ser importantes
        )
        return await self.repo.create_channel(new_channel)


# Instancia global
publisher_service = PublisherService()
