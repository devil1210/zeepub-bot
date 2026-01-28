import logging
from abc import ABC, abstractmethod
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
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.error import BadRequest

        from services.telegram_service import send_photo_bytes
        from utils.helpers import escapar_html, formatear_mensaje_portada, generar_slug_from_meta

        if not self.bot:
            from api.main import bot as main_bot

            self.bot = main_bot.app.bot

        options = options or {}
        thread_id = options.get("message_thread_id")

        # 1. Format and send Cover
        caption = formatear_mensaje_portada(book_data)
        cover_data = book_data.get("cover_bytes") or book_data.get("cover")

        await send_photo_bytes(
            self.bot, target_id, caption, cover_data, parse_mode="HTML", message_thread_id=thread_id
        )

        # 2. Get and Send Synopsis
        sinopsis = (
            book_data.get("description") or book_data.get("summary") or book_data.get("sinopsis")
        )

        # Fallback for OPDS synopsis fetching if not in book_data
        if not sinopsis:
            series_id = book_data.get("series_id")
            volume_id = book_data.get("volume_id")
            if series_id:
                from services.metadata_service import (
                    obtener_sinopsis_opds,
                    obtener_sinopsis_opds_volumen,
                )

                try:
                    if volume_id:
                        sinopsis = await obtener_sinopsis_opds_volumen(series_id, volume_id)
                    if not sinopsis:
                        sinopsis = await obtener_sinopsis_opds(series_id)
                except:
                    pass

        if sinopsis:
            sinopsis_esc = escapar_html(sinopsis)
            slug = generar_slug_from_meta(book_data)
            text = (
                f"<b>Sinopsis:</b>\n<blockquote>{sinopsis_esc}</blockquote>\n#{slug}"
                if slug
                else f"<b>Sinopsis:</b>\n<blockquote>{sinopsis_esc}</blockquote>"
            )
            try:
                await self.bot.send_message(
                    chat_id=target_id, text=text, parse_mode="HTML", message_thread_id=thread_id
                )
            except BadRequest as e:
                if "thread not found" in str(e).lower():
                    await self.bot.send_message(chat_id=target_id, text=text, parse_mode="HTML")

        # 3. Send Buttons/Interactive part
        if options.get("with_buttons", True):
            # Info text (Version, Date, Size)
            info_text = self._format_info_text(book_data)
            keyboard = options.get("custom_keyboard")

            if not keyboard:
                keyboard = [
                    [
                        InlineKeyboardButton("📥 Descargar", callback_data="descargar_confirm"),
                        InlineKeyboardButton("↩️ Volver", callback_data="volver_ultima"),
                    ]
                ]

            try:
                # Send Info Message
                msg_info = await self.bot.send_message(
                    chat_id=target_id,
                    text=info_text,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )

                # Send Buttons Message
                msg_buttons = await self.bot.send_message(
                    chat_id=target_id,
                    text="¿Deseas descargar este libro?",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    message_thread_id=thread_id,
                )

                # Return IDs if needed for state management
                if "state" in options:
                    options["state"]["msg_info_id"] = msg_info.message_id
                    options["state"]["msg_botones_id"] = msg_buttons.message_id

            except BadRequest as e:
                if "thread not found" in str(e).lower():
                    await self.bot.send_message(
                        chat_id=target_id, text=info_text, parse_mode="HTML"
                    )
                    await self.bot.send_message(
                        chat_id=target_id,
                        text="¿Deseas descargar este libro?",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )

        return True

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

        info_text = (
            f"📂 <b>{titulo}</b>\n"
            f"ℹ️ Versión Epub: {version}\n"
            f"📅 Actualizado: {fecha}\n"
            f"📦 Tamaño: {size_mb:.2f} MB{rating_txt}"
        )

        slug = generar_slug_from_meta(meta)
        if slug:
            info_text += f"\n#{slug}"

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

            # b. Public Link
            download_url = book_data.get("url") or book_data.get("filepath")
            public_link = download_url
            if download_url:
                # Try to short url
                try:
                    from utils.url_cache import create_short_url

                    dl_domain = config.DL_DOMAIN.rstrip("/")
                    if not dl_domain.startswith("http"):
                        dl_domain = f"https://{dl_domain}"
                    url_hash = create_short_url(download_url, book_title=book_data.get("title"))
                    public_link = f"{dl_domain}/api/dl/{url_hash}"
                except Exception:
                    pass

            link_block = f"⬇️ Descarga: {public_link}" if public_link else ""

            # c. Metadata
            metadata_block = formatear_metadata_fb(book_data)

            # d. Synopsis
            sinopsis = book_data.get("sinopsis") or book_data.get("description")
            sinopsis_block = ""
            if sinopsis:
                # Strip HTML for FB?
                # FB supports partial formatting but safer to strip complex html
                import re

                clean_syn = re.sub(r"<.*?>", "", sinopsis)
                sinopsis_block = f"Sinopsis:\n{clean_syn}"

            parts = [title_block, link_block, metadata_block, sinopsis_block]
            caption = "\n\n".join(p for p in parts if p).strip()

        # 3. Get Cover URL
        cover_url = book_data.get("cover_url") or book_data.get("portada")

        # If no public URL, we might need to upload bytes...
        # Current logic is URL based.
        if not cover_url or not cover_url.startswith("http"):
            # Attempt to use 'cover' if it is a URL
            c = book_data.get("cover")
            if isinstance(c, str) and c.startswith("http"):
                cover_url = c

        if not cover_url or not cover_url.startswith("http"):
            logger.error("Facebook requires a public cover URL.")
            return False

        # 4. Post to Graph API
        try:
            url = f"https://graph.facebook.com/{config.FACEBOOK_GROUP_ID}/photos"
            params = {
                "url": cover_url,
                "caption": caption,
                "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(url, params=params, timeout=30)
                if resp.status_code != 200:
                    logger.error(f"FB Error: {resp.text}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Error publishing to Facebook: {e}")
            return False


class PublisherService:
    def __init__(self, default_provider: PublisherProvider = None):
        self.providers = {
            "telegram": default_provider or TelegramPublisherProvider(),
            "facebook": FacebookPublisherProvider(),
        }

    async def announce(
        self,
        platform: str,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        provider = self.providers.get(platform)
        if not provider:
            return False
        return await provider.announce_book(target_id, book_data, options)


publisher_service = PublisherService()
