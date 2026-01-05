from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends, Header
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import httpx
import os
import hmac
import hashlib
import json
from config.config_settings import config
from services.opds_service import get_cached_feed
from utils.helpers import (
    build_search_url,
    formatear_mensaje_portada,
    find_zeepubs_destino,
    abs_url,
)
from utils.security import validate_telegram_data
from utils.http_client import fetch_bytes
from services.epub_service import (
    parse_opf_from_epub,
    extract_cover_from_epub,
    extract_internal_title,
)
from services.user_service import get_effective_user, get_user_info
import logging


from api.deps import get_telegram_user_id, get_current_user_data, require_mini_app_access

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/feed")
async def get_feed(
    url: Optional[str] = None,
    admin_mode: bool = False,
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """
    Obtiene el feed OPDS.
    """
    current_uid = user_data.get("user_id", 0)
    role = user_data.get("role", "free")
    is_admin = role == "admin"
    has_evil_access = is_admin or role == "staff"

    # Determinar URL base si no se proporciona o es raíz
    if not url or url == "/":
        if is_admin and admin_mode:
            target_url = config.OPDS_ROOT_EVIL
        else:
            target_url = config.OPDS_ROOT_START
    else:
        # Security: Prevent unauthorized users from accessing Evil Root manually
        if not has_evil_access and (
            config.OPDS_ROOT_EVIL_SUFFIX in url or config.OPDS_ROOT_EVIL in url
        ):
            logger.warning(
                f"Unauthorized {current_uid} (Role: {role}) tried to access Evil Root: {url}"
            )
            target_url = config.OPDS_ROOT_START
        else:
            target_url = url

    logger.info(f"Fetching feed from target_url: {target_url}")
    try:
        feed = await get_cached_feed(target_url)
        if not feed:
            raise HTTPException(status_code=404, detail="No se pudo cargar el feed")

        from urllib.parse import urljoin

        # Helper para normalizar URLs
        def normalize_url(href):
            if not href:
                return None
            if href.startswith("http"):
                return href

            # Use the actual feed URL as base for relative links
            return urljoin(target_url, href)

        # Convertir feedparser object a dict serializable
        entries = []
        titles_to_exclude = {
            "en el puente",
            "listas de lectura",
            "deseo leer",
            "todas las colecciones",
        }
        # For Evil Root, only keep these
        titles_to_keep_evil = {
            "actualizado recientemente",
            "añadido recientemente",
            "todas las bibliotecas",
            "all libraries",
        }

        is_root = not url or url == "/"

        for entry in getattr(feed, "entries", []):
            title = entry.get("title", "Sin título")
            title_low = title.lower()

            # Filtering logic
            if is_root:
                if admin_mode:
                    # Aggressive filtering for Evil Root
                    if title_low not in titles_to_keep_evil:
                        continue
                else:
                    # Standard filtering for Standard Root
                    if title_low in titles_to_exclude:
                        continue
            else:
                # In sub-feeds, we generally don't filter by title (we want to see books/folders)
                pass

            # Special handling for "Todas las bibliotecas" for non-admins
            if not is_admin and (
                title == "Todas las bibliotecas" or title == "All libraries"
            ):
                title = "Biblioteca Zeepubs"
                # Try to find direct link to ZeePubs ES
                try:
                    # We might need to fetch the subsection to find the direct link if it's not immediate
                    # But find_zeepubs_destino works on a FEED object.
                    # Here 'feed' is the current feed we are iterating.
                    # check if this entry is the one pointing to libraries
                    libraries_url = None
                    for link in getattr(entry, "links", []):
                        if link.get("rel") == "subsection":
                            libraries_url = normalize_url(link.get("href"))
                            break

                    if libraries_url:
                        # Fetch that feed to find ZeePubs
                        lib_feed = await get_cached_feed(libraries_url)
                        direct_url = find_zeepubs_destino(
                            lib_feed, prefer_libraries=True
                        )
                        if direct_url:
                            # Level 2 deep-link: Find the first library within the ZeePubs list
                            sub_lib_feed = await get_cached_feed(direct_url)
                            deep_link = None
                            for sub_entry in getattr(sub_lib_feed, "entries", []):
                                for sub_link in getattr(sub_entry, "links", []):
                                    if sub_link.get("rel") == "subsection":
                                        deep_link = normalize_url(sub_link.get("href"))
                                        break
                                if deep_link:
                                    break

                            entry_override_url = deep_link or direct_url
                        else:
                            entry_override_url = None
                    else:
                        entry_override_url = None

                except Exception as e:
                    logger.warning(f"Error resolving direct link for ZeePubs: {e}")
                    entry_override_url = None
            else:
                entry_override_url = None

            cover_url = None
            subsection_url = None

            # Buscar cover y subsection en links
            for link in getattr(entry, "links", []):
                link_type = link.get("type", "")
                link_rel = link.get("rel", "")
                if (
                    "image" in link_type
                    or "cover" in link_rel
                    or link_rel == "http://opds-spec.org/image"
                ):
                    cover_url = normalize_url(link.get("href"))
                elif link_rel == "subsection":
                    # Use override if available
                    if entry_override_url:
                        subsection_url = entry_override_url
                    else:
                        subsection_url = normalize_url(link.get("href"))

            # Buscar cover en content
            if not cover_url and hasattr(entry, "content"):
                for content in entry.content:
                    if "image" in content.get("type", ""):
                        cover_url = normalize_url(content.get("value"))
                        break

            # Extra metadata
            publisher = entry.get("dc_publisher") or entry.get("dcterms_publisher")
            language = entry.get("dc_language") or entry.get("dcterms_language")
            published = entry.get("published") or entry.get("issued")
            year = published[:4] if published and len(published) >= 4 else None

            isbn = None
            identifier = entry.get("identifier")
            if identifier and "isbn" in identifier.lower():
                isbn = identifier.split(":")[-1]

            detail_url = None
            size = None
            file_type = None

            for link in getattr(entry, "links", []):
                rel = link.get("rel", "")
                l_type = link.get("type", "")
                href = normalize_url(link.get("href"))

                if rel == "self" or rel == "alternate" or "type=entry" in l_type:
                    if not detail_url or rel == "self":
                        detail_url = href
                elif "acquisition" in rel or "epub" in l_type:
                    file_type = l_type
                    size = link.get("contentlength") or link.get("length")

            # Fallback for detail_url: if missing, use ID after normalization
            if not detail_url and entry.get("id"):
                detail_url = normalize_url(entry.get("id"))

            entries.append(
                {
                    "title": title,
                    "author": entry.get("author", "Desconocido"),
                    "summary": entry.get("summary", ""),
                    "id": entry.get("id", ""),
                    "cover_url": cover_url,
                    "subsection_url": subsection_url,
                    "detail_url": detail_url,
                    "publisher": publisher,
                    "language": language,
                    "isbn": isbn,
                    "year": year,
                    "size": size,
                    "file_type": file_type,
                    "links": [
                        {
                            "href": normalize_url(l.get("href")),
                            "rel": l.get("rel"),
                            "type": l.get("type"),
                        }
                        for l in getattr(entry, "links", [])
                    ],
                }
            )

        # 3. Add "Todas las colecciones" to specific sub-feeds as requested
        sub_feeds = ["/on-deck", "/reading-list", "/want-to-read"]
        if any(sub in target_url for sub in sub_feeds):
            # Find base OPDS URL to point collections link correctly
            base_opds = target_url
            for sub in sub_feeds:
                if sub in base_opds:
                    base_opds = base_opds.split(sub)[0]
                    break

            entries.append(
                {
                    "id": "injected-collections",
                    "title": "Todas las colecciones",
                    "author": "Sistema",
                    "summary": "Navegar por todas las colecciones",
                    "cover_url": None,
                    "subsection_url": f"{base_opds.rstrip('/')}/collections",
                    "detail_url": None,
                    "links": [
                        {
                            "rel": "subsection",
                            "href": f"{base_opds.rstrip('/')}/collections",
                            "type": "application/atom+xml;profile=opds-catalog;kind=navigation",
                        }
                    ],
                }
            )

        # Second pass: fetch covers for folders that don't have one
        import asyncio

        async def fetch_folder_cover(res):
            if res["subsection_url"] and not res["cover_url"]:
                try:
                    sub_feed = await get_cached_feed(res["subsection_url"])
                    sub_entries = getattr(sub_feed, "entries", [])
                    if sub_entries:
                        first_book = sub_entries[0]
                        for l in getattr(first_book, "links", []):
                            l_type = l.get("type", "")
                            l_rel = l.get("rel", "")
                            if (
                                "image" in l_type
                                or "cover" in l_rel
                                or l_rel == "http://opds-spec.org/image"
                            ):
                                res["cover_url"] = normalize_url(l.get("href"))
                                break
                except httpx.HTTPStatusError as e:
                    logger.warning(
                        f"HTTP error fetching sub-feed {res['subsection_url']}: {e}"
                    )
                except httpx.RequestError as e:
                    logger.warning(
                        f"Request error fetching sub-feed {res['subsection_url']}: {e}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Unexpected error fetching sub-feed {res['subsection_url']}: {e}"
                    )

        folder_tasks = [
            fetch_folder_cover(e)
            for e in entries
            if e["subsection_url"] and not e["cover_url"]
        ]
        if folder_tasks:
            # We process sequential for the main feed to avoid overloading the OPDS server
            # but we use a small concurrency limit
            await asyncio.gather(*folder_tasks[:10])

        # Extract pagination links from feed.links
        next_page = None
        prev_page = None
        first_page = None
        last_page = None

        for link in getattr(feed.feed, "links", []):
            rel = link.get("rel", "")
            href = normalize_url(link.get("href"))
            if rel == "next":
                next_page = href
            elif rel == "previous" or rel == "prev":
                prev_page = href
            elif rel == "first":
                first_page = href
            elif rel == "last":
                last_page = href

        # Try to guess current page
        current_page = 1
        if url and "page=" in url:
            import urllib.parse

            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            try:
                current_page = int(params.get("page", [1])[0])
            except ValueError:
                logger.debug(f"Could not parse page number from URL: {url}")
            except Exception as e:
                logger.warning(f"Unexpected error parsing page number from URL: {e}")

        # Total pages
        total_pages = None
        total_results = feed.feed.get("opensearch_totalresults")
        items_per_page = feed.feed.get("opensearch_itemsperpage")
        if total_results and items_per_page:
            try:
                total_pages = (int(total_results) + int(items_per_page) - 1) // int(
                    items_per_page
                )
            except ValueError:
                logger.debug(
                    f"Could not calculate total pages from results={total_results}, items_per_page={items_per_page}"
                )
            except Exception as e:
                logger.warning(f"Unexpected error calculating total pages: {e}")
        processed_links = [
            {
                "href": normalize_url(l.get("href")),
                "rel": l.get("rel"),
                "type": l.get("type"),
            }
            for l in getattr(feed.feed, "links", [])
        ]

        return {
            "title": getattr(feed.feed, "title", "ZeePub Feed"),
            "links": processed_links,
            "entries": entries,
            "nextPage": next_page,
            "prevPage": prev_page,
            "firstPage": first_page,
            "lastPage": last_page,
            "currentPage": current_page,
            "totalPages": total_pages,
        }
    except HTTPException as e:
        raise e
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching feed: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error fetching feed: {e.response.text}",
        )
    except httpx.RequestError as e:
        logger.error(f"Request error fetching feed: {e}")
        raise HTTPException(status_code=500, detail=f"Network error fetching feed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_books(
    q: str = Query(..., min_length=1),
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """
    Busca libros en el servidor OPDS.
    """
    current_uid = user_data.get("user_id", 0)
    # Usamos el UID validado para construir la URL de búsqueda (si es necesario)
    search_url = build_search_url(q, uid=current_uid)
    return await get_feed(url=search_url, user_data=user_data)


@router.get("/image/{rest_of_path:path}")
async def proxy_image(rest_of_path: str, request: Request):
    """
    Proxies image requests to the upstream OPDS server.
    """
    try:
        upstream_base = config.OPDS_SERVER_URL.rstrip("/")
        # Try both /api/image and direct paths
        full_url = f"{upstream_base}/api/image/{rest_of_path}"
        query_params = dict(request.query_params)

        headers = {"User-Agent": "ZeePubBot/4.5 (Proxy)", "Accept": "image/*, */*"}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            logger.info(f"Proxying image: {full_url} with params {query_params}")
            resp = await client.get(
                full_url, params=query_params, auth=config.OPDS_AUTH, headers=headers
            )

            if resp.status_code == 404:
                # Fallback to direct path
                alt_url = f"{upstream_base}/{rest_of_path}"
                logger.debug(f"Image 404 at {full_url}, trying {alt_url}")
                resp = await client.get(
                    alt_url, params=query_params, auth=config.OPDS_AUTH, headers=headers
                )

            resp.raise_for_status()

            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "image/jpeg"),
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        logger.error(f"Image proxy error for {rest_of_path}: {e}")
        raise HTTPException(status_code=404, detail="Image not found")


@router.get("/bot/avatar")
async def bot_avatar_proxy(file_id: str = Query(...)):
    """
    Proxies the bot's profile photo from Telegram.
    """
    from api.main import bot
    try:
        file = await bot.app.bot.get_file(file_id)
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
        logger.error(f"Error proxying bot avatar {file_id}: {e}")
        # Fallback to the local librarian image via redirect or local read
        # For simplicity and robustness, lets just tell the browser to use the local one
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/robot-librarian.jpg")


@router.get("/tunnel/opds")
async def tunnel_opds(
    url: str = Query(..., description="Target OPDS URL"),
    admin_mode: bool = Query(False, description="Whether to show full admin catalog"),
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """
    Proxies OPDS requests directly to the server, injecting credentials.
    Returns raw XML or modified XML for UI improvements.
    """
    current_uid = user_data.get("user_id", 0)

    # Normalize URL: support root fallback and relative paths
    if not url or url == "/":
        if user_data.get("role") == "admin" and admin_mode:
            target_url = config.OPDS_ROOT_EVIL
        else:
            target_url = config.OPDS_ROOT_START
    elif not url.startswith("http"):
        base = config.OPDS_SERVER_URL.rstrip("/")
        if url.startswith("/"):
            target_url = f"{base}{url}"
        else:
            target_url = f"{base}/{url}"
    else:
        target_url = url

    logger.info(
        f"Tunneling OPDS -> {target_url} for user {current_uid} (admin_mode={admin_mode})"
    )

    headers = {
        "User-Agent": "ZeePubBot/4.5 (OPDS Tunnel)",
        "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(target_url, auth=config.OPDS_AUTH, headers=headers)

            if r.status_code >= 400:
                logger.error(
                    f"Upstream OPDS error {r.status_code} for {target_url}: {r.text[:200]}"
                )
                return Response(
                    content=f"Error upstream: {r.status_code}",
                    status_code=r.status_code,
                )

            content_type = r.headers.get("content-type", "")

            # If it's XML, we might want to modify it (renaming, relinking)
            if "xml" in content_type and (
                user_data.get("role") != "admin" or not admin_mode
            ):
                import re

                xml_text = r.text

                # 1. Rename and Relink "Todas las bibliotecas" -> "Biblioteca Zeepubs"
                if "Todas las bibliotecas" in xml_text:
                    xml_text = xml_text.replace(
                        "Todas las bibliotecas", "Biblioteca Zeepubs"
                    )
                    # Relink /libraries -> /libraries/1 for direct library access
                    xml_text = re.sub(
                        r'/libraries(?=["\s/])(?!/1)', "/libraries/1", xml_text
                    )

                # 2. Hide unwanted sections from the ROOT feed (Mi Catálogo)
                if "<id>root</id>" in xml_text or "<id>libraries</id>" in xml_text:
                    to_hide = [
                        "En el puente",
                        "Listas de lectura",
                        "Deseo leer",
                        "Todas las colecciones",
                        "Actualizado recientemente",
                        "Añadido recientemente",
                    ]
                    for title in to_hide:
                        # Refined pattern: ensure we don't cross <entry> boundaries
                        pattern = rf"<entry>(?:(?!</entry>)[\s\S])*?<title>{re.escape(title)}</title>[\s\S]*?</entry>"
                        xml_text = re.sub(pattern, "", xml_text)

                # 3. Add "Todas las colecciones" to specific sub-feeds as requested
                sub_feeds = ["/on-deck", "/reading-list", "/want-to-read"]
                if (
                    any(sub in target_url for sub in sub_feeds)
                    and "</feed>" in xml_text
                ):
                    # Find base OPDS URL to point collections link correctly
                    base_opds = target_url
                    for sub in sub_feeds:
                        if sub in base_opds:
                            base_opds = base_opds.split(sub)[0]
                            break

                    extra_entry = f"""
  <entry>
    <updated>2025-12-26T12:00:00</updated>
    <id>allCollections-injected</id>
    <title>Todas las colecciones</title>
    <content type="text">Navegar por colecciones</content>
    <link rel="subsection" type="application/atom+xml;profile=opds-catalog;kind=navigation" href="{base_opds}/collections" />
  </entry>
"""
                    xml_text = xml_text.replace("</feed>", extra_entry + "</feed>")

                return Response(
                    content=xml_text.encode("utf-8"), media_type=content_type
                )

            # For non-XML (binary icons, etc), stream it
            return StreamingResponse(r.aiter_bytes(), media_type=content_type)

    except Exception as e:
        logger.error(f"Tunnel exception for {target_url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


from utils.url_cache import get_url_from_hash


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
        from urllib.parse import unquote, urlparse

        parsed = urlparse(url)
        title = unquote(parsed.path.split("/")[-1]).replace(".epub", "")

        # Redirigir al endpoint público
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=f"/api/public/dl?url={url}&title={title}")
    except Exception as e:
        logger.error(f"Error decoding short URL: {e}")
        raise HTTPException(status_code=404, detail="Invalid short URL")


@router.get("/public/dl")
async def public_download(
    url: str = Query(..., description="Source EPUB URL"),
    title: str = Query("libro", description="Filename hint"),
):
    """
    Proxy público para descargas.
    Sirve el archivo desde la fuente OPDS original.
    """
    try:
        # Validar URL básica para evitar SSRF flagrante (aunque fetch_bytes ya es genérico)
        if not url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid URL")

        # Usar fetch_bytes para obtener el contenido (memoria o archivo temp)
        # Nota: fetch_bytes maneja archivos grandes escribiendo a disco
        import aiohttp

        auth = None
        if config.OPDS_AUTH:
            auth = aiohttp.BasicAuth(config.OPDS_AUTH[0], config.OPDS_AUTH[1])

        data = await fetch_bytes(url, timeout=120, auth=auth)

        if not data:
            raise HTTPException(status_code=404, detail="Could not fetch file")

        from fastapi.responses import StreamingResponse

        # Determinar si es archivo o bytes
        if isinstance(data, str) and os.path.exists(data):
            # Es un archivo temporal - usar aiofiles para streaming async
            import aiofiles

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
                        logger.debug(
                            "Could not remove temp file from streaming proxy: %s", e
                        )

            return StreamingResponse(
                content=iterfile_async(),
                media_type="application/epub+zip",
                headers={"Content-Disposition": f'attachment; filename="{title}.epub"'},
            )
        else:
            # Son bytes en memoria
            # StreamingResponse espera un iterador o bytes-like object?
            # Response normal funciona para bytes.
            return Response(
                content=data,
                media_type="application/epub+zip",
                headers={"Content-Disposition": f'attachment; filename="{title}.epub"'},
            )

    except Exception as e:
        logger.error(f"Error in public download proxy: {e}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.post("/facebook/prepare")
async def prepare_facebook_post(
    request: Request,
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
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
                l["href"]
                for l in book.get("links", [])
                if "acquisition" in l.get("rel", "") or "epub" in l.get("type", "")
            ),
            None,
        )
        cover_url = book.get("cover_url")

        if not download_url:
            raise HTTPException(status_code=400, detail="No download URL found")

        # Construir link público acortado con SHA256
        from utils.url_cache import create_short_url
        from urllib.parse import quote, unquote, urlparse

        dl_domain = config.DL_DOMAIN.rstrip("/")
        # Asegurar esquema
        if not dl_domain.startswith("http"):
            dl_domain = f"https://{dl_domain}"

        # Crear hash y guardar en BD SQLite
        url_hash = create_short_url(download_url)
        public_link = f"{dl_domain}/api/dl/{url_hash}"

        # Intentar obtener metadatos completos del EPUB para el título
        header_title = f"📚 <b>{title}</b>"  # Fallback

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
                filename_title = unquote(
                    urlparse(download_url).path.split("/")[-1]
                ).replace(".epub", "")
                meta["filename_title"] = filename_title

                # Debug logging
                logger.info(
                    f"FB Post Meta - internal_title: {meta.get('internal_title')}, collection_title: {meta.get('titulo_serie')}, titulo_volumen: {meta.get('titulo_volumen')}"
                )

                # Generar caption completo (sin slug para FB)
                full_caption = formatear_mensaje_portada(meta, include_slug=False)

                # Usar el caption completo
                caption_base = full_caption

        except Exception as e:
            logger.warning(f"Could not fetch/parse EPUB for FB post: {e}")
            caption_base = f"📚 <b>{title}</b>"  # Fallback

        caption = f"{caption_base}\n\n" f"⬇️ <b>Descarga directa:</b>\n" f"{public_link}"

        return {"caption": caption, "cover_url": cover_url, "public_link": public_link}

    except Exception as e:
        logger.error(f"Error preparing FB post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/facebook/publish")
async def publish_facebook_post(
    request: Request,
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
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
        clean_msg = (
            error_msg.replace("<b>", "")
            .replace("</b>", "")
            .replace("<code>", "")
            .replace("</code>", "")
        )
        raise HTTPException(status_code=400, detail=clean_msg)

    try:
        data = await request.json()
        caption = data.get("caption")
        cover_url = data.get(
            "cover_url"
        )  # URL de la portada (debe ser pública para que FB la vea, o subimos bytes)

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
            "caption": caption.replace("<b>", "").replace(
                "</b>", ""
            ),  # FB no soporta HTML tags básicos así
            "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, params=params, timeout=30)
            resp.raise_for_status()
            fb_data = resp.json()

        return {"success": True, "fb_id": fb_data.get("id")}

    except Exception as e:
        logger.error(f"Error publishing to FB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config(user_data: Dict[str, Any] = Depends(require_mini_app_access)):
    """
    Retorna configuración inicial para la Mini App, incluyendo permisos de admin y publisher.
    """
    current_uid = user_data.get("user_id", 0)
    is_admin = current_uid in config.ADMIN_USERS
    is_publisher = current_uid in config.FACEBOOK_PUBLISHERS

    response = {
        "is_admin": is_admin,
        "is_facebook_publisher": is_publisher,
        "admin_root_url": config.OPDS_ROOT_EVIL if is_admin else None,
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
        destinations.append(
            {"name": "📍 Aquí (Vista Previa FB)", "id": "me_fb_preview"}
        )

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
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
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
            raise HTTPException(
                status_code=400, detail="Missing required fields or authentication"
            )

        logger.info(
            f"Download request from user {user_id}: {title} -> {target_chat_id}"
        )

        from api.main import bot
        from services.telegram_service import enviar_libro_directo

        # Determinar formato y destino real
        format_type = "standard"
        real_target = target_chat_id

        if target_chat_id == "me_fb_preview":
            format_type = "fb_preview"
            real_target = user_id  # Enviar al usuario
        elif target_chat_id == "facebook_group":
            format_type = "fb_direct"
            real_target = None  # Se maneja internamente con config
        elif target_chat_id == "me":
            real_target = user_id

        success = await enviar_libro_directo(
            bot.app.bot,
            user_id=user_id,
            title=title,
            download_url=download_url,
            cover_url=cover_url,
            target_chat_id=real_target,
            format_type=format_type,
        )

        if success:
            return {"status": "success", "message": "Operation completed"}
        else:
            raise HTTPException(status_code=500, detail="Operation failed")

    except Exception as e:
        logger.error(f"Error in download endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zitadel-action")
async def zitadel_enrich_token(request: Request):
    """
    Endpoint para ZITADEL Actions v2 (Function: preuserinfo).
    Enriquece el token con roles de Kavita y preferred_username.
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
                    logger.error(
                        f"⛔ Invalid ZITADEL signature from IP: {request.client.host}"
                    )
                    raise HTTPException(status_code=401, detail="Invalid signature")
        else:
            logger.warning(
                "⚠️ ZITADEL_SIGNING_KEY not configured - skipping signature validation"
            )

        # Parsear el JSON que envía ZITADEL
        try:
            data = json.loads(body_bytes)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

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
            preferred_username = (
                safe_str(human_data.get("email")) if human_data else None
            )

        # 1. Agregar preferred_username si se encontró
        if preferred_username:
            claims_list.append(
                {"key": "preferred_username", "value": preferred_username}
            )

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
        raise HTTPException(status_code=500, detail="Error processing action")
