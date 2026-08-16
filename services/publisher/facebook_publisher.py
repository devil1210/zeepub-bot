import logging
import os
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

    # Limpiar y formatear caption para Facebook eliminando 'Pulsa aquí' y convirtiendo links a texto plano
    from utils.helpers import clean_caption_for_facebook
    fb_caption = clean_caption_for_facebook(fb_caption, public_link=public_link)

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
                    accounts = resp.json().get("data", [])
                    found = False
                    for acc in accounts:
                        if str(acc.get("id")) == str(target_id):
                            token = acc.get("access_token", token)
                            found = True
                            break
                    if not found and len(accounts) == 1:
                        target_id = str(accounts[0].get("id"))
                        token = accounts[0].get("access_token", token)
        except Exception:
            pass

        fb_cover_url = cover_url or meta.get("portada")
        from services.cover_service import resolve_cover_data
        resolved_cover = await resolve_cover_data(fb_cover_url) if fb_cover_url else None

        url_upload = f"https://graph.facebook.com/v19.0/{target_id}/photos"
        params_upload = {
            "access_token": token,
            "published": "false",
        }

        try:
            async with httpx.AsyncClient() as client:
                photo_id = None
                if isinstance(resolved_cover, bytes):
                    files = {"source": ("cover.jpg", resolved_cover, "image/jpeg")}
                    resp_up = await client.post(url_upload, params=params_upload, files=files, timeout=45)
                    if resp_up.status_code in (200, 201):
                        photo_id = resp_up.json().get("id")
                elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                    with open(resolved_cover, "rb") as f:
                        files = {"source": ("cover.jpg", f.read(), "image/jpeg")}
                        resp_up = await client.post(url_upload, params=params_upload, files=files, timeout=45)
                        if resp_up.status_code in (200, 201):
                            photo_id = resp_up.json().get("id")
                elif fb_cover_url and fb_cover_url.startswith("http"):
                    params_upload["url"] = fb_cover_url
                    resp_up = await client.post(url_upload, params=params_upload, timeout=45)
                    if resp_up.status_code in (200, 201):
                        photo_id = resp_up.json().get("id")

                # Publicar en el muro ("Publicaciones") vía /feed
                url_feed = f"https://graph.facebook.com/v19.0/{target_id}/feed"
                payload_feed: dict[str, Any] = {"message": fb_caption}
                if photo_id:
                    payload_feed["attached_media"] = [{"media_fbid": str(photo_id)}]

                resp_feed = await client.post(
                    url_feed,
                    params={"access_token": token},
                    json=payload_feed,
                    timeout=45,
                )

                if resp_feed.status_code not in (200, 201):
                    logger.error(f"FB Feed Error: {resp_feed.text}")
                    await bot.send_message(chat_id=user_id, text=f"❌ Error publicando en el muro de Facebook: {resp_feed.text}")
                    return False

            await bot.send_message(chat_id=user_id, text="✅ Publicado exitosamente en el muro de Facebook.")
            return True
        except Exception as e:
            logger.error(f"Excepción publicando en Facebook: {e}")
            await bot.send_message(chat_id=user_id, text=f"❌ Excepción publicando en Facebook: {e}")
            return False

    return False
