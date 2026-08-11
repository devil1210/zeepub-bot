import logging
import re
from typing import Any

import httpx

from config.settings import config
from services.cover_service import send_photo_bytes
from services.publisher.publisher_service import TelegramPublisherProvider
from utils.helpers import validate_facebook_credentials
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
        url_hash = create_short_url(download_url, book_title=title) if download_url else "N/A"
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

    # Limpiar HTML residual (FB no soporta HTML tags)
    fb_caption = re.sub(r"<[^>]+>", "", fb_caption).strip()

    # Añadir link de descarga si existe y no está incluido en la plantilla
    if public_link and public_link not in fb_caption and "http" not in fb_caption:
        fb_caption = f"{fb_caption}\n\n⬇️ Descarga: {public_link}"

    # Truncar si excede el límite de FB
    if len(fb_caption) > 2100:
        fb_caption = fb_caption[:2097] + "..."

    logger.debug(f"Caption FB generado vía template engine, longitud: {len(fb_caption)}")

    if format_type == "fb_preview":
        if portada_data:
            await send_photo_bytes(bot, user_id, None, portada_data, filename="cover.jpg")
        await bot.send_message(
            chat_id=user_id,
            text=fb_caption,
            disable_web_page_preview=False,
        )
        return True

    elif format_type == "fb_direct":
        is_valid, error_msg = validate_facebook_credentials(config)
        if not is_valid:
            await bot.send_message(chat_id=user_id, text=error_msg, parse_mode="HTML")
            return False

        target_id = config.FACEBOOK_GROUP_ID
        token = config.FACEBOOK_PAGE_ACCESS_TOKEN

        # Intentar resolver Page Access Token si es un User Token
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get("https://graph.facebook.com/v19.0/me/accounts", params={"access_token": token}, timeout=10)
                if resp.status_code == 200:
                    for acc in resp.json().get("data", []):
                        if str(acc.get("id")) == str(target_id):
                            token = acc.get("access_token", token)
                            break
        except Exception:
            pass

        fb_cover_url = cover_url or meta.get("portada")
        from services.cover_service import resolve_cover_data
        resolved_cover = await resolve_cover_data(fb_cover_url) if fb_cover_url else None

        url = f"https://graph.facebook.com/v19.0/{target_id}/photos"
        params = {
            "caption": fb_caption,
            "access_token": token,
        }

        try:
            async with httpx.AsyncClient() as client:
                if isinstance(resolved_cover, bytes):
                    files = {"source": ("cover.jpg", resolved_cover, "image/jpeg")}
                    resp = await client.post(url, params=params, files=files, timeout=45)
                elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                    with open(resolved_cover, "rb") as f:
                        files = {"source": ("cover.jpg", f.read(), "image/jpeg")}
                        resp = await client.post(url, params=params, files=files, timeout=45)
                elif fb_cover_url and fb_cover_url.startswith("http"):
                    params["url"] = fb_cover_url
                    resp = await client.post(url, params=params, timeout=45)
                else:
                    await bot.send_message(chat_id=user_id, text="⚠️ No se pudo obtener la portada del libro para Facebook.")
                    return False

                if resp.status_code not in (200, 201):
                    logger.error(f"FB Error: {resp.text}")
                    await bot.send_message(chat_id=user_id, text=f"❌ Error publicando en Facebook: {resp.text}")
                    return False

            await bot.send_message(chat_id=user_id, text="✅ Publicado exitosamente en Facebook.")
            return True
        except Exception as e:
            logger.error(f"Excepción publicando en Facebook: {e}")
            await bot.send_message(chat_id=user_id, text=f"❌ Excepción publicando en Facebook: {e}")
            return False

    return False
