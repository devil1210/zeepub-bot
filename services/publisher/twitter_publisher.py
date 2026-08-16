import base64
import hashlib
import hmac
import logging
import os
import re
import time
import urllib.parse
from typing import Any

import httpx

from config.config_settings import config

logger = logging.getLogger(__name__)


def generate_oauth1_header(
    method: str,
    url: str,
    params: dict[str, str],
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
) -> str:
    """Genera la cabecera de autenticación OAuth 1.0a para la API de X / Twitter."""
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": os.urandom(16).hex(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }

    all_params = {**oauth_params, **params}
    sorted_params = sorted(
        (urllib.parse.quote(str(k), safe=""), urllib.parse.quote(str(v), safe=""))
        for k, v in all_params.items()
    )
    param_string = "&".join(f"{k}={v}" for k, v in sorted_params)

    base_string = "&".join(
        [
            method.upper(),
            urllib.parse.quote(url, safe=""),
            urllib.parse.quote(param_string, safe=""),
        ]
    )

    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_token_secret, safe='')}"

    hashed = hmac.new(
        signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1
    )
    signature = base64.b64encode(hashed.digest()).decode("utf-8")
    oauth_params["oauth_signature"] = signature

    header_parts = [
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    ]
    return "OAuth " + ", ".join(header_parts)


async def post_to_twitter(
    text_content: str,
    cover_data: bytes | str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    access_token: str | None = None,
    access_token_secret: str | None = None,
) -> bool:
    """Publica un Tweet en X (Twitter) v2 con soporte opcional para imagen adjunta."""
    api_key = api_key or config.TWITTER_API_KEY
    api_secret = api_secret or config.TWITTER_API_SECRET
    access_token = access_token or config.TWITTER_ACCESS_TOKEN
    access_token_secret = access_token_secret or config.TWITTER_ACCESS_TOKEN_SECRET

    if not all([api_key, api_secret, access_token, access_token_secret]):
        logger.error("⚠️ Credenciales de X / Twitter incompletas o no configuradas.")
        return False

    # Resolver imagen si existe
    media_ids = []
    if cover_data:
        image_bytes = None
        if isinstance(cover_data, bytes):
            image_bytes = cover_data
        elif isinstance(cover_data, str) and os.path.exists(cover_data):
            try:
                with open(cover_data, "rb") as f:
                    image_bytes = f.read()
            except Exception as e:
                logger.warning(f"Error al leer imagen para Twitter: {e}")

        if image_bytes:
            try:
                upload_url = "https://upload.twitter.com/1.1/media/upload.json"
                header = generate_oauth1_header(
                    "POST",
                    upload_url,
                    {},
                    api_key,
                    api_secret,
                    access_token,
                    access_token_secret,
                )
                async with httpx.AsyncClient() as client:
                    files = {"media": ("cover.jpg", image_bytes, "image/jpeg")}
                    resp = await client.post(
                        upload_url,
                        headers={"Authorization": header},
                        files=files,
                        timeout=30,
                    )
                    if resp.status_code == 200:
                        media_id = resp.json().get("media_id_string")
                        if media_id:
                            media_ids.append(media_id)
                    else:
                        logger.warning(
                            f"No se pudo subir imagen a X (Twitter): {resp.text}"
                        )
            except Exception as e:
                logger.warning(f"Excepción al subir portada a X: {e}")

    # Limpiar etiquetas HTML residuales
    clean_text = re.sub(r"<[^>]+>", "", text_content).strip()
    if len(clean_text) > 280:
        clean_text = clean_text[:277] + "..."

    tweet_url = "https://api.twitter.com/2/tweets"
    header = generate_oauth1_header(
        "POST",
        tweet_url,
        {},
        api_key,
        api_secret,
        access_token,
        access_token_secret,
    )

    headers = {
        "Authorization": header,
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {"text": clean_text}
    if media_ids:
        payload["media"] = {"media_ids": media_ids}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                tweet_url, headers=headers, json=payload, timeout=30
            )
            if resp.status_code in (200, 201):
                logger.info("✅ Publicación exitosa en X (Twitter)")
                return True
            else:
                logger.error(
                    f"❌ Error al publicar en X (Twitter): {resp.status_code} {resp.text}"
                )
                return False
    except Exception as e:
        logger.error(f"Excepción al publicar en X (Twitter): {e}")
        return False
