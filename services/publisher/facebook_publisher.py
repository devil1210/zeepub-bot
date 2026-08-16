import logging
from typing import Any

from config.config_settings import config
from services.cover_service import send_photo_bytes
from services.publisher.publisher_service import (
    FacebookPublisherProvider,
    TelegramPublisherProvider,
)
from utils.template_engine import apply_publication_template
from utils.url_cache import create_short_url

logger = logging.getLogger(__name__)


async def handle_facebook_publication(
    bot,
    user_id: int,
    format_type: str,
    title: str,
    download_url: str | None,
    cover_url: str | None,
    meta: dict[str, Any],
    portada_data: bytes | None,
    caption: str | None = None,
) -> bool:
    """
    Handles formatting and publishing to Facebook or sending a Facebook preview to the user.
    """
    # Generar link público acortado
    dl_domain = config.DL_DOMAIN.rstrip("/")
    if not dl_domain.startswith("http"):
        dl_domain = f"https://{dl_domain}"
    try:
        url_hash = (
            create_short_url(download_url, book_title=title)
            if download_url
            else "N/A"
        )
        public_link = f"{dl_domain}/api/dl/{url_hash}"
    except Exception as e:
        logger.error("Error creating short URL: %s", e)
        public_link = download_url or ""

    # Generar caption FB usando la plantilla seleccionada o predeterminada
    custom_caption = caption or meta.get("caption")
    if custom_caption:
        fb_caption = custom_caption
    elif meta.get("template_content"):
        fb_caption = apply_publication_template(meta["template_content"], meta)
    else:
        fb_caption = apply_publication_template(
            TelegramPublisherProvider.FB_CAPTION_TEMPLATE, meta
        )

    # Limpiar y formatear caption para Facebook eliminando 'Pulsa aquí' y convirtiendo links a texto plano
    from utils.helpers import clean_caption_for_facebook

    fb_caption = clean_caption_for_facebook(fb_caption, public_link=public_link)

    logger.debug(
        f"Caption FB generado vía template engine, longitud: {len(fb_caption)}"
    )

    if format_type == "fb_preview":
        if portada_data:
            await send_photo_bytes(
                bot, user_id, None, portada_data, filename="cover.jpg"
            )
        await bot.send_message(
            chat_id=user_id,
            text=fb_caption,
            disable_web_page_preview=False,
        )
        return True

    elif format_type == "fb_direct":
        provider = FacebookPublisherProvider()

        book_data = {
            "id": meta.get("id") or meta.get("book_hash") or meta.get("hash"),
            "book_hash": meta.get("book_hash") or meta.get("hash"),
            "title": title,
            "series": meta.get("series") or meta.get("series_name"),
            "series_spanish": meta.get("series_spanish")
            or meta.get("series_name")
            or meta.get("series"),
            "series_id": meta.get("series_id") or meta.get("series_hash"),
            "cover_high": cover_url or meta.get("portada"),
            "cover_original": cover_url or meta.get("portada"),
            "portada": cover_url or meta.get("portada"),
            "public_link": public_link,
            "download_link": public_link,
        }
        book_data.update(meta)

        success = await provider.announce_book(
            target_id=config.FACEBOOK_GROUP_ID,
            book_data=book_data,
            options={"caption": fb_caption},
        )

        if success:
            await bot.send_message(
                chat_id=user_id,
                text="✅ Publicado exitosamente en Facebook (organizado en álbum de serie si aplica).",
            )
            return True
        else:
            await bot.send_message(
                chat_id=user_id,
                text="❌ Error al procesar la publicación en Facebook. Revisa los logs o credenciales.",
            )
            return False

    return False
