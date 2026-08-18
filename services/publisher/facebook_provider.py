import logging
import os
from typing import Any

from services.publisher.base import PublisherProvider
from services.publisher.telegram_provider import TelegramPublisherProvider
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


class FacebookPublisherProvider(PublisherProvider):
    """
    Proveedor para publicación en Facebook Pages/Groups:
    - Agrupación automática en Álbumes por Serie (POST /{album_id}/photos)
    - Fallback a Feed general con foto adjunta
    - Persistencia de fb_post_id y fb_photo_id en BD
    - Capacidad de edición de publicaciones (POST /{post_id})
    """

    async def _resolve_credentials(
        self, target_id: str | int | None, token: str
    ) -> tuple[str, str]:
        """Resuelve el Page ID y Page Access Token si se proveyó un User Token."""
        import httpx
        from config.config_settings import config

        target_page_id = str(target_id) if target_id else config.FACEBOOK_GROUP_ID
        page_token = token

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://graph.facebook.com/v19.0/me/accounts",
                    params={"access_token": token},
                    timeout=10,
                )
                if resp.status_code == 200:
                    accounts = resp.json().get("data", [])
                    found = False
                    for acc in accounts:
                        if str(acc.get("id")) == str(target_page_id):
                            page_token = acc.get("access_token", token)
                            found = True
                            break
                    if not found and len(accounts) == 1:
                        target_page_id = str(accounts[0].get("id"))
                        page_token = accounts[0].get("access_token", token)
        except Exception as e:
            logger.debug(f"No se pudo resolver Page Token vía /me/accounts: {e}")

        return target_page_id, page_token

    async def get_or_create_series_album(
        self,
        target_page_id: str,
        token: str,
        series_name: str,
        series_id: str | None = None,
        alt_names: list[str] | None = None,
    ) -> str | None:
        """
        Obtiene el ID del álbum de la serie o lo busca en Facebook con soporte de nombres alternativos.
        Persiste el fb_album_id en el registro de Series.
        """
        if not series_name or not series_name.strip():
            return None

        clean_series_name = series_name.strip()
        all_candidates = [clean_series_name]
        if alt_names:
            for an in alt_names:
                if an and an.strip() and an.strip() not in all_candidates:
                    all_candidates.append(an.strip())

        # 1. Verificar si ya tenemos el fb_album_id en la base de datos
        if series_id:
            try:
                from core.db_manager_pg import pg_manager
                from models.library import Series
                from sqlalchemy import select

                async with pg_manager.get_session() as session:
                    stmt = select(Series.fb_album_id).where(Series.id == series_id)
                    result = await session.execute(stmt)
                    cached_album_id = result.scalar_one_or_none()
                    if cached_album_id:
                        logger.info(
                            f"Álbum en caché para '{clean_series_name}': {cached_album_id}"
                        )
                        return str(cached_album_id)
            except Exception as e:
                logger.debug(f"Error consultando fb_album_id en BD: {e}")

        import httpx

        # 2. Buscar en la lista de álbumes de la página vía Graph API
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://graph.facebook.com/v19.0/{target_page_id}/albums",
                    params={"access_token": token, "fields": "id,name", "limit": 100},
                    timeout=20,
                )
                if resp.status_code == 200:
                    albums = resp.json().get("data", [])
                    # Paso A: Coincidencia exacta (case-insensitive) con cualquiera de los candidatos
                    for album in albums:
                        alb_name = album.get("name", "").strip().lower()
                        for cand in all_candidates:
                            if alb_name == cand.lower():
                                found_id = str(album.get("id"))
                                logger.info(
                                    f"Álbum exacto encontrado en Facebook: '{cand}' -> {album.get('name')} (ID: {found_id})"
                                )
                                await self._persist_series_album_id(series_id, found_id)
                                return found_id

                    # Paso B: Coincidencia parcial / substring si el nombre es representativo (>= 4 caracteres)
                    for album in albums:
                        alb_name = album.get("name", "").strip().lower()
                        if alb_name in (
                            "fotos",
                            "fotos del perfil",
                            "fotos de portada",
                            "mobile uploads",
                        ):
                            continue
                        for cand in all_candidates:
                            c_low = cand.lower()
                            if len(c_low) >= 4 and (
                                c_low in alb_name or alb_name in c_low
                            ):
                                found_id = str(album.get("id"))
                                logger.info(
                                    f"Álbum parcial encontrado en Facebook: '{cand}' -> {album.get('name')} (ID: {found_id})"
                                )
                                await self._persist_series_album_id(series_id, found_id)
                                return found_id

                # 3. Si no existe, intentar crear nuevo álbum
                payload_create = {
                    "name": clean_series_name,
                    "message": f"Álbum oficial de la serie: {clean_series_name}",
                }
                create_resp = await client.post(
                    f"https://graph.facebook.com/v19.0/{target_page_id}/albums",
                    params={"access_token": token},
                    data=payload_create,
                    timeout=25,
                )
                if create_resp.status_code in (200, 201):
                    new_album_id = str(create_resp.json().get("id"))
                    logger.info(
                        f"✅ Nuevo álbum creado en Facebook: '{clean_series_name}' -> {new_album_id}"
                    )
                    await self._persist_series_album_id(series_id, new_album_id)
                    return new_album_id
                else:
                    logger.warning(
                        f"⚠️ Álbum para '{clean_series_name}' no existe en Facebook. Para que se agrupen los libros, crea un álbum en tu Página con el nombre exacto: '{clean_series_name}'"
                    )
        except Exception as e:
            logger.error(f"Excepción al gestionar álbum de Facebook: {e}")

        return None

    async def check_album_exists(
        self,
        target_page_id: str | int | None,
        token: str,
        series_name: str,
        series_id: str | None = None,
        alt_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Verifica si existe el álbum en Facebook y entrega el nombre específico recomendado.
        """
        resolved_page_id, page_token = await self._resolve_credentials(
            target_page_id, token
        )

        clean_series_name = series_name.strip() if series_name else ""
        all_candidates = [clean_series_name] if clean_series_name else []
        if alt_names:
            for an in alt_names:
                if an and an.strip() and an.strip() not in all_candidates:
                    all_candidates.append(an.strip())

        recommended_name = clean_series_name or (
            alt_names[0] if alt_names else "Serie"
        )

        if not resolved_page_id or not page_token:
            return {
                "exists": False,
                "album_id": None,
                "album_name": None,
                "recommended_name": recommended_name,
                "candidates": all_candidates,
                "error": "Credenciales de Facebook no configuradas",
            }

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://graph.facebook.com/v19.0/{resolved_page_id}/albums",
                    params={
                        "access_token": page_token,
                        "fields": "id,name",
                        "limit": 100,
                    },
                    timeout=15,
                )
                if resp.status_code == 200:
                    albums = resp.json().get("data", [])
                    available_albums = [
                        {
                            "id": str(alb.get("id")),
                            "name": str(alb.get("name")),
                        }
                        for alb in albums
                        if alb.get("name")
                    ]
                    # Exact match
                    for album in albums:
                        alb_name = album.get("name", "").strip().lower()
                        for cand in all_candidates:
                            if alb_name == cand.lower():
                                found_id = str(album.get("id"))
                                await self._persist_series_album_id(series_id, found_id)
                                return {
                                    "exists": True,
                                    "album_id": found_id,
                                    "album_name": album.get("name"),
                                    "recommended_name": recommended_name,
                                    "candidates": all_candidates,
                                    "available_albums": available_albums,
                                    "page_id": resolved_page_id,
                                }
                    # Partial match
                    for album in albums:
                        alb_name = album.get("name", "").strip().lower()
                        if alb_name in (
                            "fotos",
                            "fotos del perfil",
                            "fotos de portada",
                            "mobile uploads",
                        ):
                            continue
                        for cand in all_candidates:
                            c_low = cand.lower()
                            if len(c_low) >= 4 and (
                                c_low in alb_name or alb_name in c_low
                            ):
                                found_id = str(album.get("id"))
                                await self._persist_series_album_id(series_id, found_id)
                                return {
                                    "exists": True,
                                    "album_id": found_id,
                                    "album_name": album.get("name"),
                                    "recommended_name": recommended_name,
                                    "candidates": all_candidates,
                                    "available_albums": available_albums,
                                    "page_id": resolved_page_id,
                                }

                    return {
                        "exists": False,
                        "album_id": None,
                        "album_name": None,
                        "recommended_name": recommended_name,
                        "candidates": all_candidates,
                        "available_albums": available_albums,
                        "page_id": resolved_page_id,
                    }
                else:
                    return {
                        "exists": False,
                        "album_id": None,
                        "album_name": None,
                        "recommended_name": recommended_name,
                        "candidates": all_candidates,
                        "available_albums": [],
                        "error": f"Facebook API error: {resp.status_code}",
                    }
        except Exception as e:
            return {
                "exists": False,
                "album_id": None,
                "album_name": None,
                "recommended_name": recommended_name,
                "candidates": all_candidates,
                "available_albums": [],
                "error": str(e),
            }

    async def _persist_series_album_id(
        self, series_id: str | None, album_id: str
    ) -> None:
        """Helper para guardar fb_album_id en Series."""
        if not series_id or not album_id:
            return
        try:
            from core.db_manager_pg import pg_manager
            from models.library import Series
            from sqlalchemy import update

            async with pg_manager.get_session() as session:
                await session.execute(
                    update(Series)
                    .where(Series.id == series_id)
                    .values(fb_album_id=album_id)
                )
                await session.commit()
        except Exception as e:
            logger.debug(f"No se pudo persistir fb_album_id en Series: {e}")

    async def _persist_book_fb_ids(
        self, book_hash: str | None, post_id: str | None, photo_id: str | None
    ) -> None:
        """Helper para guardar fb_post_id y fb_photo_id en Book."""
        if not book_hash or (not post_id and not photo_id):
            return
        try:
            from core.db_manager_pg import pg_manager
            from models.library import Book
            from sqlalchemy import update

            async with pg_manager.get_session() as session:
                values = {}
                if post_id:
                    values["fb_post_id"] = str(post_id)
                if photo_id:
                    values["fb_photo_id"] = str(photo_id)
                await session.execute(
                    update(Book).where(Book.id == book_hash).values(**values)
                )
                await session.commit()
        except Exception as e:
            logger.debug(f"No se pudo persistir fb_post_id en Book: {e}")

    async def publish_photo_to_album(
        self,
        album_id: str,
        resolved_cover: Any,
        cover_source: Any,
        caption: str,
        token: str,
    ) -> dict[str, Any] | None:
        """Sube una foto dentro de un álbum y luego aplica el caption por separado.

        Se hace en dos pasos para evitar corrupción de emojis UTF-8 en multipart/form-data:
        1. Subir la foto (sin mensaje para evitar encoding issues)
        2. Actualizar el caption con update_post_message (POST simple sin files)
        """
        import httpx

        url_upload = f"https://graph.facebook.com/v19.0/{album_id}/photos"
        params_upload = {"access_token": token}

        try:
            async with httpx.AsyncClient() as client:
                resp = None
                if isinstance(resolved_cover, bytes):
                    files = {"source": ("cover.jpg", resolved_cover, "image/jpeg")}
                    resp = await client.post(
                        url_upload,
                        params=params_upload,
                        files=files,
                        timeout=45,
                    )
                elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                    with open(resolved_cover, "rb") as f:
                        files = {"source": ("cover.jpg", f.read(), "image/jpeg")}
                        resp = await client.post(
                            url_upload,
                            params=params_upload,
                            files=files,
                            timeout=45,
                        )
                elif cover_source and str(cover_source).startswith("http"):
                    # Para URLs remotas: enviar directamente con message (no hay archivo)
                    resp = await client.post(
                        url_upload,
                        params=params_upload,
                        data={"url": str(cover_source), "message": caption},
                        timeout=45,
                    )

                if resp and resp.status_code in (200, 201):
                    data = resp.json()
                    photo_id = data.get("id")
                    post_id = data.get("post_id") or photo_id

                    # Paso 2: Aplicar caption correctamente en POST /{post_id} con "message" (form-urlencoded)
                    # Esto garantiza 100% preservación de emojis UTF-8 en Facebook Graph API
                    if caption and post_id:
                        try:
                            caption_resp = await client.post(
                                f"https://graph.facebook.com/v19.0/{post_id}",
                                params={"access_token": token},
                                data={"message": caption},
                                timeout=30,
                            )
                            if caption_resp.status_code not in (200, 201):
                                logger.warning(
                                    f"No se pudo aplicar caption al post {post_id}: {caption_resp.text}"
                                )
                            else:
                                logger.info(
                                    f"✅ Caption con emojis aplicado con éxito al post {post_id} en Facebook."
                                )
                        except Exception as ce:
                            logger.warning(f"Error aplicando caption: {ce}")

                    return {"photo_id": photo_id, "post_id": post_id}
                elif resp:
                    logger.warning(
                        f"Error subiendo foto al álbum {album_id}: {resp.text}"
                    )
        except Exception as e:
            logger.error(f"Excepción subiendo foto al álbum {album_id}: {e}")

        return None

    async def update_post_message(
        self,
        post_id: str,
        new_message: str,
        token: str | None = None,
        target_id: str | int | None = None,
    ) -> bool:
        """
        Edita el mensaje/texto y enlaces de una publicación o foto existente en Facebook.
        Graph API: POST /{post-id} con parámetro 'message'.
        """
        if not post_id or not new_message:
            return False

        import httpx
        from config.config_settings import config

        base_token = token or config.get_facebook_token(target_id)
        _, page_token = await self._resolve_credentials(target_id, base_token)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://graph.facebook.com/v19.0/{post_id}",
                    params={"access_token": page_token},
                    data={"message": new_message},
                    timeout=30,
                )
                if resp.status_code in (200, 201):
                    logger.info(
                        f"✅ Publicación {post_id} actualizada exitosamente en Facebook."
                    )
                    return True
                else:
                    logger.error(f"Error actualizando post {post_id}: {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Excepción actualizando post {post_id}: {e}")
            return False

    async def announce_book(
        self,
        target_id: str | int,
        book_data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> bool:
        options = options or {}
        caption = options.get("caption")

        if not caption:
            # Intentar resolver la plantilla por defecto de Facebook configurada en BD
            try:
                from core.db_manager_pg import pg_manager
                from models.communications import PublicationTemplate
                from sqlalchemy import select

                async with pg_manager.get_session() as session:
                    stmt = (
                        select(PublicationTemplate)
                        .where(PublicationTemplate.platform == "facebook")
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
                logger.debug(f"No se pudo cargar plantilla de BD para Facebook: {e}")

        if not caption:
            caption = apply_publication_template(
                TelegramPublisherProvider.FB_CAPTION_TEMPLATE, book_data
            )

        from utils.helpers import clean_caption_for_facebook

        fb_caption = clean_caption_for_facebook(caption)

        cover_source = (
            book_data.get("cover_high")
            or book_data.get("cover_original")
            or book_data.get("portada")
        )

        from config.config_settings import config
        from utils.helpers import validate_facebook_credentials

        explicit_token = options.get("page_access_token") or options.get("token")
        if not explicit_token:
            is_valid, error_msg = validate_facebook_credentials(config, target_id=target_id)
            if not is_valid:
                logger.error(f"Error publicando en Facebook: {error_msg}")
                return False

        resolved_raw_token = explicit_token or config.get_facebook_token(target_id)
        target_group_id, token = await self._resolve_credentials(
            target_id, resolved_raw_token
        )

        from services.cover_service import resolve_cover_data

        resolved_cover = (
            await resolve_cover_data(cover_source) if cover_source else None
        )

        book_hash = book_data.get("id") or book_data.get("book_hash")
        series_spanish = book_data.get("series_spanish")
        series_orig = book_data.get("series_name") or book_data.get("series")
        title = book_data.get("title")

        alt_names = []
        for n in [series_spanish, series_orig, title]:
            if n and n.strip() and n.strip() not in alt_names:
                alt_names.append(n.strip())
            if n and ":" in n:
                prefix = n.split(":")[0].strip()
                if prefix and prefix not in alt_names:
                    alt_names.append(prefix)
            if n and " - " in n:
                prefix = n.split(" - ")[0].strip()
                if prefix and prefix not in alt_names:
                    alt_names.append(prefix)
            if n and "." in n:
                prefix = n.split(".")[0].strip()
                if prefix and prefix not in alt_names:
                    alt_names.append(prefix)

        series_name = series_spanish or series_orig or title
        series_id = book_data.get("series_id") or book_data.get("series_hash")

        chosen_album_id = options.get("fb_album_id") or options.get("album_id")

        # 1. Caso A: Si se seleccionó expresamente "none" o "wall", no usar ningún álbum
        if chosen_album_id in ("none", "wall", "feed"):
            logger.info(
                "Publicación en Facebook configurada expresamente para Muro principal (sin álbum)."
            )
        # 2. Caso B: Si se seleccionó un álbum específico de la lista
        elif chosen_album_id and chosen_album_id != "auto":
            logger.info(
                f"Subiendo foto a álbum de Facebook seleccionado: {chosen_album_id}"
            )
            upload_res = await self.publish_photo_to_album(
                str(chosen_album_id), resolved_cover, cover_source, fb_caption, token
            )
            if upload_res:
                photo_id = upload_res.get("photo_id")
                post_id = upload_res.get("post_id") or photo_id
                await self._persist_book_fb_ids(book_hash, post_id, photo_id)
                if series_id:
                    await self._persist_series_album_id(
                        series_id, str(chosen_album_id)
                    )
                logger.info(
                    f"✅ Publicado exitosamente en Álbum seleccionado {chosen_album_id} de Facebook (Post: {post_id})"
                )
                return True
            else:
                logger.warning(
                    f"Fallo al publicar en álbum seleccionado {chosen_album_id}, recurriendo a feed principal..."
                )
        # 3. Caso C: Detección automática habitual por nombre de serie
        elif series_name:
            album_id = await self.get_or_create_series_album(
                target_group_id, token, series_name, series_id, alt_names=alt_names
            )
            if album_id:
                upload_res = await self.publish_photo_to_album(
                    album_id, resolved_cover, cover_source, fb_caption, token
                )
                if upload_res:
                    photo_id = upload_res.get("photo_id")
                    post_id = upload_res.get("post_id") or photo_id
                    await self._persist_book_fb_ids(book_hash, post_id, photo_id)
                    logger.info(
                        f"✅ Publicado exitosamente en Álbum '{series_name}' de Facebook (Post: {post_id})"
                    )
                    return True
                else:
                    logger.warning(
                        f"Fallo al publicar en álbum '{series_name}', recurriendo a feed principal..."
                    )

        # 2. Fallback al muro / feed principal
        import httpx

        url_upload = f"https://graph.facebook.com/v19.0/{target_group_id}/photos"
        params_upload = {
            "access_token": token,
            "published": "false",
        }

        try:
            async with httpx.AsyncClient() as client:
                photo_id = None
                if isinstance(resolved_cover, bytes):
                    files = {"source": ("cover.jpg", resolved_cover, "image/jpeg")}
                    resp_up = await client.post(
                        url_upload, params=params_upload, files=files, timeout=45
                    )
                    if resp_up.status_code in (200, 201):
                        photo_id = resp_up.json().get("id")
                elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
                    with open(resolved_cover, "rb") as f:
                        files = {"source": ("cover.jpg", f.read(), "image/jpeg")}
                        resp_up = await client.post(
                            url_upload, params=params_upload, files=files, timeout=45
                        )
                        if resp_up.status_code in (200, 201):
                            photo_id = resp_up.json().get("id")
                elif cover_source and str(cover_source).startswith("http"):
                    params_upload["url"] = str(cover_source)
                    resp_up = await client.post(
                        url_upload, params=params_upload, timeout=45
                    )
                    if resp_up.status_code in (200, 201):
                        photo_id = resp_up.json().get("id")

                url_feed = f"https://graph.facebook.com/v19.0/{target_group_id}/feed"
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
                    return False

                feed_data = resp_feed.json()
                post_id = feed_data.get("id")
                await self._persist_book_fb_ids(book_hash, post_id, photo_id)

            logger.info(
                f"✅ Publicado exitosamente en el Muro de Facebook (Página {target_group_id}, Post {post_id})"
            )
            return True
        except Exception as e:
            logger.error(f"Excepción al publicar en Facebook: {e}")
            return False
