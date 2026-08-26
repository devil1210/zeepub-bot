import hashlib
import hmac
import json
import logging
import os
from typing import Annotated, Any
from urllib.parse import unquote, urlparse

import aiofiles
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from api.deps import (
    require_mini_app_access,
)
from config.config_settings import config
from services.epub_service import extract_internal_title, parse_opf_from_epub
from utils.http_client import fetch_bytes
from utils.url_cache import get_url_from_hash

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/bot/avatar")
async def bot_avatar_proxy(file_id: str = Query(...)):
    """
    Proxies the bot's profile photo from Telegram.
    """
    from api.main import bot

    try:
        logger.info(f"Proxying bot avatar for file_id: {file_id}")
        file = await bot.app.bot.get_file(file_id)
        if not file.file_path:
            logger.error(f"No file_path found for file_id: {file_id}")
            from fastapi.responses import RedirectResponse

            return RedirectResponse(url="/robot-librarian.jpg")

        # Use httpx to download and stream to client
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(file.file_path)
            resp.raise_for_status()

            return Response(
                content=resp.content,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=31536000"},  # Cache for a year
            )
    except Exception as e:
        logger.error(f"Error proxying bot avatar {file_id}: {e}", exc_info=True)
        # Fallback to the local librarian image via redirect or local read
        # For simplicity and robustness, lets just tell the browser to use the local one
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/robot-librarian.jpg")


@router.get("/dl/{url_hash}")
async def short_download(url_hash: str):
    """
    Endpoint acortado para descargas usando hash SHA256.
    """
    try:
        # Buscar en BD SQLite
        url = get_url_from_hash(url_hash)
        if not url:
            raise HTTPException(status_code=404, detail="Short URL not found")

        # Extraer título del final de la URL

        parsed = urlparse(url)
        title = unquote(parsed.path.split("/")[-1]).replace(".epub", "")

        # Llamar directamente a la lógica de descarga pública (proxy)
        # Esto evita redirecciones que expongan la URL real en el navegador
        return await public_download(url=url, title=title)
    except Exception as e:
        logger.error(f"Error decoding short URL: {e}")
        raise HTTPException(status_code=404, detail="Invalid short URL") from e


@router.get("/public/dl")
async def public_download(
    url: str = Query(..., description="Source EPUB URL or Local Path"),
    title: str = Query("libro", description="Filename hint"),
):
    """
    Proxy público para descargas.
    Sirve el archivo desde una URL remota o un path local.
    """
    try:
        # 1. Caso Path Local
        if os.path.exists(url) and os.path.isfile(url):
            from fastapi.responses import FileResponse

            logger.info(f"Serving local file: {url}")
            return FileResponse(
                path=url,
                media_type="application/epub+zip",
                filename=f"{title}.epub",
            )

        # 2. Caso URL Remota (Mantenemos compatibilidad por si acaso, pero sin OPDS_AUTH)
        if not url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid URL or file not found")

        logger.info(f"Proxying remote download: {url}")
        data = await fetch_bytes(url, timeout=120)

        if not data:
            raise HTTPException(status_code=404, detail="Could not fetch file")

        # Determinar si es archivo o bytes
        if isinstance(data, str) and os.path.exists(data):
            # Es un archivo temporal - usar aiofiles para streaming async

            async def iterfile_async():
                try:
                    async with aiofiles.open(data, mode="rb") as f:
                        chunk = await f.read(64 * 1024)
                        while chunk:
                            yield chunk
                            chunk = await f.read(64 * 1024)
                finally:
                    try:
                        os.unlink(data)
                    except Exception as e:
                        logger.debug("Could not remove temp file from streaming proxy: %s", e)

            return StreamingResponse(
                content=iterfile_async(),
                media_type="application/epub+zip",
                headers={"Content-Disposition": f'attachment; filename="{title}.epub"'},
            )
        else:
            return Response(
                content=data,
                media_type="application/epub+zip",
                headers={"Content-Disposition": f'attachment; filename="{title}.epub"'},
            )

    except Exception as e:
        logger.error(f"Error in public download proxy: {e}")
        raise HTTPException(status_code=500, detail="Download failed") from e


@router.post("/facebook/prepare")
async def prepare_facebook_post(
    request: Request,
    user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
):
    """
    Prepara el texto y link para un post de Facebook.
    """
    current_uid = user_data.get("user_id", 0)
    if current_uid not in config.FACEBOOK_PUBLISHERS:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        data = await request.json()
        book = data.get("book")
        if not book:
            raise HTTPException(status_code=400, detail="Missing book data")

        # Extraer datos
        title = book.get("title", "Libro")
        download_url = next(
            (
                link_obj["href"]
                for link_obj in book.get("links", [])
                if "acquisition" in link_obj.get("rel", "") or "epub" in link_obj.get("type", "")
            ),
            None,
        )
        cover_url = book.get("cover_url")

        if not download_url:
            raise HTTPException(status_code=400, detail="No download URL found")

        # Construir link público acortado con SHA256

        from utils.url_cache import create_short_url

        dl_domain = config.DL_DOMAIN.rstrip("/")
        # Asegurar esquema
        if not dl_domain.startswith("http"):
            dl_domain = f"https://{dl_domain}"

        # Crear hash y guardar en BD SQLite
        url_hash = create_short_url(download_url)
        public_link = f"{dl_domain}/api/dl/{url_hash}"

        # Intentar obtener metadatos completos del EPUB para el título

        try:
            # Descargar primeros bytes o todo para parsear
            epub_bytes = await fetch_bytes(download_url, timeout=60)
            if epub_bytes:
                meta = {
                    "titulo": title,
                    "epub_version": "2.0",
                    "fecha_modificacion": "Desconocida",
                }

                # Parsear OPF
                opf_meta = await parse_opf_from_epub(epub_bytes)
                if opf_meta:
                    meta.update(opf_meta)

                # Extraer título interno
                internal_title = extract_internal_title(epub_bytes)
                if internal_title:
                    meta["internal_title"] = internal_title

                # Extraer filename title
                filename_title = unquote(urlparse(download_url).path.split("/")[-1]).replace(".epub", "")
                meta["filename_title"] = filename_title

                # Debug logging
                logger.info(
                    f"FB Post Meta - internal_title: {meta.get('internal_title')}, collection_title: {meta.get('titulo_serie')}, titulo_volumen: {meta.get('titulo_volumen')}"
                )

                # Generar caption completo (sin slug para FB) usando el motor unificado
                from services.publisher.publisher_service import (
                    TelegramPublisherProvider,
                )
                from utils.template_engine import apply_publication_template

                # Enriquecer meta con tamaño si no está
                if "file_size" not in meta and epub_bytes:
                    meta["file_size"] = len(epub_bytes)

                caption_base = apply_publication_template(TelegramPublisherProvider.FB_CAPTION_TEMPLATE, meta)

        except Exception as e:
            logger.warning(f"Could not fetch/parse EPUB for FB post: {e}")
            caption_base = f"📚 <b>{title}</b>"  # Fallback

        caption = f"{caption_base}\n\n⬇️ <b>Descarga directa:</b>\n{public_link}"

        return {"caption": caption, "cover_url": cover_url, "public_link": public_link}

    except Exception as e:
        logger.error(f"Error preparing FB post: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/facebook/publish")
async def publish_facebook_post(
    request: Request,
    user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
):
    """
    Publica en el grupo de Facebook configurado.
    """
    current_uid = user_data.get("user_id", 0)
    if current_uid not in config.FACEBOOK_PUBLISHERS:
        raise HTTPException(status_code=403, detail="Not authorized")

    from utils.helpers import validate_facebook_credentials

    is_valid, error_msg = validate_facebook_credentials(config)

    if not is_valid:
        # Strip HTML for API error detail
        clean_msg = error_msg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
        raise HTTPException(status_code=400, detail=clean_msg)

    try:
        data = await request.json()
        caption = data.get("caption")
        cover_url = data.get("cover_url")  # URL de la portada (debe ser pública para que FB la vea, o subimos bytes)

        # Nota: Para subir foto a FB, se puede pasar URL si es pública.
        # Si nuestra URL de portada es local/proxy, FB podría no verla si no es pública real.
        # Asumimos que cover_url es accesible o usamos el proxy de imagen si es público.

        # Si la cover_url es relativa o interna, intentar resolverla
        if cover_url and not cover_url.startswith("http"):
            cover_url = f"{config.BASE_URL}{cover_url}"

        # Lógica de publicación en Graph API
        url = f"https://graph.facebook.com/{config.FACEBOOK_GROUP_ID}/photos"
        params = {
            "url": cover_url,
            "caption": caption.replace("<b>", "").replace("</b>", ""),  # FB no soporta HTML tags básicos así
            "access_token": config.get_facebook_token(config.FACEBOOK_GROUP_ID),
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params, timeout=30)
            resp.raise_for_status()
            fb_data = resp.json()

        return {"success": True, "fb_id": fb_data.get("id")}

    except Exception as e:
        logger.error(f"Error publishing to FB: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/config")
async def get_config(user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)]):
    """
    Retorna configuración inicial para la Mini App, incluyendo permisos de admin y publisher.
    """
    current_uid = user_data.get("user_id", 0)
    is_admin = current_uid in config.ADMIN_USERS
    is_publisher = current_uid in config.FACEBOOK_PUBLISHERS

    response = {
        "is_admin": is_admin,
        "is_facebook_publisher": is_publisher,
        "destinations": [],
    }

    # Definir destinos según roles
    destinations = []

    # 1. Opción "Aquí" (Privado)
    # 1. Opción "Aquí" (Privado) - Siempre disponible para admins y publishers
    if is_admin or is_publisher:
        destinations.append({"name": "📍 Aquí (Chat privado)", "id": "me"})

    if is_publisher:
        # Publishers ven TAMBIÉN la vista previa de FB
        destinations.append({"name": "📍 Aquí (Vista Previa FB)", "id": "me_fb_preview"})

    # 2. Canales de Admin
    if is_admin:
        destinations.extend(
            [
                {"name": "📣 ZeePubs Channel", "id": "@ZeePubs"},
                {"name": "🤖 ZeePub Bot Test", "id": "@ZeePubBotTest"},
            ]
        )

    # 3. Grupos de Publisher
    if is_publisher:
        destinations.append({"name": "👥 Grupo de Facebook", "id": "facebook_group"})

    response["destinations"] = destinations

    return response


@router.get("/app-strings")
async def get_app_strings(request: Request):
    """
    Obtiene los textos personalizados para la Mini App.
    """
    bot_instance = getattr(request.app.state, "bot_instance", None)
    if not bot_instance or not bot_instance.plugin_manager:
        # Fallback si no hay bot o plugins
        from plugins.custom_messages_plugin import TEMPLATE_REGISTRY

        return {
            slug.replace("web_", ""): entry["default"]
            for slug, entry in TEMPLATE_REGISTRY.items()
            if slug.startswith("web_")
        }

    plugin = bot_instance.plugin_manager.get_plugin("custom_messages")
    if not plugin:
        from plugins.custom_messages_plugin import TEMPLATE_REGISTRY

        return {
            slug.replace("web_", ""): entry["default"]
            for slug, entry in TEMPLATE_REGISTRY.items()
            if slug.startswith("web_")
        }

    return await plugin.get_web_strings()


@router.post("/download")
async def download_book(
    request: Request,
    user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
):
    """
    Handle EPUB download requests from Mini App.
    """
    try:
        data = await request.json()
        title = data.get("title", "Libro")
        download_url = data.get("download_url")
        cover_url = data.get("cover_url")
        target_chat_id = data.get("target_chat_id")

        # Validar que el usuario autenticado coincida con el solicitado (o simplemente usar el autenticado)
        user_id = user_data.get("user_id", 0)

        if not download_url or not user_id:
            raise HTTPException(status_code=400, detail="Missing required fields or authentication")

        logger.info(f"Download request from user {user_id}: {title} -> {target_chat_id}")

        from api.main import bot
        from services.delivery.delivery_service import DeliveryService

        # Determinar formato y destino real
        real_target = target_chat_id
        options = {
            "target_chat_id": target_chat_id,
            "auto_delete_seconds": 0,
        }

        if target_chat_id == "me_fb_preview":
            options["format_type"] = "fb_preview"
            real_target = user_id  # Enviar al usuario
        elif target_chat_id == "facebook_group":
            options["format_type"] = "fb_direct"
            real_target = user_id  # O el que corresponda
        elif target_chat_id == "me":
            real_target = user_id

        # Preparar book_data para el provider
        book_data = {
            "title": title,
            "url": download_url,
            "cover_url": cover_url,
        }

        # Usar DeliveryService para que se apliquen las plantillas y demás lógica centralizada
        delivery_service = DeliveryService(bot=bot.app.bot)
        success = await delivery_service.deliver_book(
            provider_type="telegram", target_id=real_target or user_id, book_data=book_data, options=options
        )

        if success:
            return {"status": "success", "message": "Operation completed"}
        else:
            raise HTTPException(status_code=500, detail="Operation failed")

    except Exception as e:
        logger.error(f"Error in download endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/zitadel-action")
async def zitadel_enrich_token(request: Request):
    """
    Endpoint para ZITADEL Actions v2 (Function: preuserinfo).
    Enriquece el token con roles y preferred_username.
    """
    try:
        # Leer body raw
        body_bytes = await request.body()

        # Validar firma de ZITADEL (opcional)
        signature = request.headers.get("x-zitadel-signature")

        # Si tenemos signing key configurada, validamos
        if config.ZITADEL_SIGNING_KEY:
            if not signature:
                logger.warning("⚠️ ZITADEL action received without signature header")
                raise HTTPException(status_code=401, detail="Missing signature")
            else:
                # Calcular HMAC SHA256
                expected_signature = hmac.new(
                    config.ZITADEL_SIGNING_KEY.encode("utf-8"),
                    body_bytes,
                    hashlib.sha256,
                ).hexdigest()

                # Comparación segura contra timing attacks
                if not hmac.compare_digest(signature, expected_signature):
                    logger.error(f"⛔ Invalid ZITADEL signature from IP: {request.client.host}")
                    raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning("⚠️ ZITADEL_SIGNING_KEY not configured - skipping signature validation")

        # Parsear el JSON que envía ZITADEL
        try:
            data = json.loads(body_bytes)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from e

        logger.debug(f"Payload received: {data}")

        # Helper para validación
        def safe_str(val):
            """Extrae string válido o None"""
            return val.strip() if isinstance(val, str) and val and val.strip() else None

        # Extraer contextos
        user_data = data.get("user", {})
        human_data = user_data.get("human", {})
        claims_list = []

        # Calcular preferred_username
        preferred_username = None
        if human_data:
            # 1. Nickname
            preferred_username = safe_str(human_data.get("nick_name"))

            # 2. Display Name
            if not preferred_username:
                preferred_username = safe_str(human_data.get("display_name"))

            # 3. First + Last Name (concatenación inteligente)
            if not preferred_username:
                first = safe_str(human_data.get("first_name"))
                last = safe_str(human_data.get("last_name"))
                if first and last:
                    preferred_username = f"{first} {last}"
                elif first:
                    preferred_username = first

        # 4. Username base (fallback)
        if not preferred_username:
            preferred_username = safe_str(user_data.get("username"))

        # 5. Email (último recurso)
        if not preferred_username:
            preferred_username = safe_str(human_data.get("email")) if human_data else None

        # 1. Agregar preferred_username si se encontró
        if preferred_username:
            claims_list.append({"key": "preferred_username", "value": preferred_username})

        # 2. Agregar roles fijos para todos los usuarios de ZeePubs
        claims_list.append(
            {
                "key": "https://zeepubs.com/roles",
                "value": [
                    "Login",
                    "Download",
                    "Change Password",
                    "Bookmark",
                    "library-EpubLibre [ES]",
                    "library-EpubShosetsu [ES]",
                    "library-MiraiK [ES]",
                    "library-WhiteMoon [EN]",
                    "library-ZeePubs [ES]",
                ],
            }
        )

        # 3. Respuesta final
        response = {"append_claims": claims_list}

        logger.info(f"✅ Token enriched for user: {preferred_username}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions (ya tienen logging)
        raise
    except Exception as e:
        logger.error(f"❌ Error processing ZITADEL action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing action") from e
