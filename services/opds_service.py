import uuid
import logging
from functools import wraps
import re
from urllib.parse import urlparse, unquote
from difflib import SequenceMatcher
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# from core.state_manager import state_manager (Moved to local scope)
from config.config_settings import config
from utils.http_client import parse_feed_from_url
from utils.helpers import (
    abs_url,
    find_zeepubs_destino,
    extract_author,
    parse_metadata_from_title,
)
from services.cache_service import AsyncTTLCache

logger = logging.getLogger(__name__)

# Cache global para OPDS feeds (6 horas TTL)
opds_cache = AsyncTTLCache(ttl_seconds=21600)


async def get_cached_feed(url: str):
    """Obtiene feed del caché o lo descarga."""
    cached = await opds_cache.get(url)
    if cached:
        logger.debug(f"Cache hit for {url}")
        return cached

    logger.debug(f"Cache miss for {url}, downloading...")
    feed = await parse_feed_from_url(url)
    if feed and getattr(feed, "entries", []):
        await opds_cache.set(url, feed)
    return feed


async def mostrar_colecciones(
    update,
    context: ContextTypes.DEFAULT_TYPE,
    url: str,
    from_collection: bool = False,
    new_message: bool = False,
):
    """Mostrar colecciones o libros basados en un feed OPDS."""
    uid = update.effective_user.id
    from core.state_manager import state_manager

    st = state_manager.get_user_state(uid)

    # Inicializar historial si no existe
    if "historial" not in st:
        st["historial"] = []

    # Usar get_cached_feed en lugar de parse_feed_from_url directo
    feed = await get_cached_feed(url)

    if not feed or not getattr(feed, "entries", []):
        msg = "❌ No se pudo leer el feed o no hay resultados."
        if hasattr(update, "message") and update.message:
            await update.message.reply_text(msg)
        else:
            await update.callback_query.edit_message_text(msg)
        return

    root_url = st.get("opds_root")

    # Actualizar estado (sin tocar historial, lo gestiona el handler)
    # ... (rest of logic unchanged, just ensuring we cache successful feeds)
    st.update(
        {
            "url": url,
            "libros": {},
            "colecciones": {},
            "nav": {"prev": None, "next": None},
        }
    )

    # enlaces de navegación (paginación dentro de la misma biblioteca)
    logger.debug(f"Total links en feed: {len(getattr(feed.feed, 'links', []))}")
    for link in getattr(feed.feed, "links", []):
        rel = getattr(link, "rel", "")
        href = abs_url(config.BASE_URL, link.href)
        logger.debug(f"Link encontrado - rel: {rel}, href: {href}")
        if rel == "prev" or rel == "previous":  # Añade "prev"
            st["nav"]["prev"] = href
        elif rel == "next":
            st["nav"]["next"] = href

    logger.debug(
        f"Final nav state - prev: {st['nav']['prev']}, next: {st['nav']['next']}"
    )

    # NO sobrescribas el prev del feed con el historial
    # El historial se usa solo para "Subir nivel", no para paginación

    colecciones, libros = [], []
    ocultos = {
        "En el puente",
        "Listas de lectura",
        "Deseo leer",
        "Todas las colecciones",
    }

    # No ocultar "Todas las bibliotecas" para admins, pero sí procesarla diferente para no-admins

    for entry in feed.entries:
        title = getattr(entry, "title", "")

        # Check if folder for correct fallback
        has_subsection = any(
            getattr(l, "rel", "") == "subsection" for l in getattr(entry, "links", [])
        )
        author = extract_author(entry, is_folder=has_subsection)
        href_entry = getattr(entry, "link", "")
        href_sub, portada = None, None
        acqs = []

        for l in getattr(entry, "links", []):
            rel = getattr(l, "rel", "")
            href_l = abs_url(config.BASE_URL, l.href)
            if rel == "subsection":
                href_sub = href_l
            elif "acquisition" in rel:
                acqs.append(href_l)
            elif "image" in rel:
                portada = href_l

        if href_sub and title not in ocultos:
            colecciones.append({"titulo": title, "href": href_sub})
        elif acqs:
            for download in acqs:
                libros.append(
                    {
                        "titulo": title,
                        "autor": author,
                        "href": href_entry,
                        "descarga": download,
                        "portada": portada,
                    }
                )

    # Título y markup
    title = st.get("titulo") or "📚 Categorías"

    # 1. Pre-procesar Storyline para la cabecera e identificar nombres extra para redundancia
    raw_feed_title = getattr(feed.feed, "title", "")
    known_romaji = None
    known_english = None

    if raw_feed_title.endswith(" - Storyline") and libros:
        # Intentar deducir la estructura English - Romaji del primer libro
        first_book_title = getattr(feed.entries[0], "title", "")
        clean_feed_title_part = raw_feed_title.replace(" - Storyline", "").strip()

        parts = first_book_title.split(" - ")
        if len(parts) >= 2:

            def clean_title_part(s):
                s = re.sub(r"\[.*?\]", "", s)
                s = re.sub(r"^[^\w\(\)]+", "", s)
                return s.strip()

            p0_clean = clean_title_part(parts[0])
            feed_clean = clean_title_part(clean_feed_title_part)

            if (
                p0_clean == feed_clean
                or p0_clean in feed_clean
                or feed_clean in p0_clean
            ):
                known_romaji = parts[1].strip()
                known_english = re.sub(r"^[^\w\(\)]+", "", parts[0]).strip()

                icon_prefix = ""
                if " " in title:
                    possible_icon = title.split(" ", 1)[0]
                    if not possible_icon.isalnum():
                        icon_prefix = possible_icon + " "

                title = f"{icon_prefix}{known_english}\n\n{known_romaji}"

    # 2. Construir teclado
    keyboard = [[InlineKeyboardButton("🔍 Buscar EPUB", callback_data="buscar")]]

    if colecciones:
        for i, col in enumerate(colecciones):
            st["colecciones"][i] = col
            titulo_boton = col["titulo"]

            if (
                uid not in config.ADMIN_USERS
                and col["titulo"] == "Todas las bibliotecas"
            ):
                titulo_boton = "📚 Biblioteca ZeePubs"

            keyboard.append(
                [InlineKeyboardButton(titulo_boton, callback_data=f"col|{i}")]
            )
    else:
        for b in libros:
            key = uuid.uuid4().hex[:8]
            st["libros"][key] = b

            feed_title = getattr(feed.feed, "title", st.get("titulo", ""))
            feed_title = feed_title.replace(" - Storyline", "")

            meta_context = parse_metadata_from_title(feed_title)
            context_series = meta_context.get("series", "").lower()

            meta = parse_metadata_from_title(b["titulo"])
            display_title = b["titulo"]

            book_tags = set(meta.get("tags", []))
            context_tags = set(meta_context.get("tags", []))
            unique_tags = sorted(list(book_tags - context_tags))

            tags_str = ""
            if unique_tags:
                tags_str = " " + " ".join([f"[{t}]" for t in unique_tags])

            clean_title = meta.get("clean_title", display_title)

            def simplify(s):
                return re.sub(r"[^\w]", "", s).lower()

            s_ctx = simplify(context_series)
            s_book = simplify(clean_title)

            # Clean tags from romaji for comparison too
            clean_romaji = re.sub(r"\[.*?\]", "", known_romaji or "").strip()
            s_romaji = simplify(clean_romaji) if clean_romaji else ""

            is_redundant = False
            if s_book:
                # 1. Direct Subset (Inglés o Romaji)
                if s_ctx and (s_ctx in s_book or s_book in s_ctx):
                    is_redundant = True
                elif s_romaji and (s_romaji in s_book or s_book in s_romaji):
                    is_redundant = True
                else:
                    # 2. Fuzzy match fallback (Permisivo para títulos largos)
                    ratio = SequenceMatcher(None, s_ctx, s_book).ratio()
                    if ratio > 0.8:
                        is_redundant = True
                    elif s_romaji:
                        ratio_r = SequenceMatcher(None, s_romaji, s_book).ratio()
                        if ratio_r > 0.7:  # Más permisivo para Romaji
                            is_redundant = True

                    # 3. Last chance: check if the full original title contains the Romaji name
                    # (Useful if tag parsing failed)
                    if (
                        not is_redundant
                        and s_romaji
                        and s_romaji in simplify(b["titulo"])
                    ):
                        is_redundant = True

            if is_redundant:
                if meta.get("volume"):
                    display_title = f"Volumen {meta['volume']}{tags_str}"
                else:
                    display_title = f"Volumen único{tags_str}"
            else:
                s_name = clean_title
                if len(s_name) > 30:
                    s_name = s_name[:27] + "..."
                display_title = f"{s_name}{tags_str}"

            keyboard.append(
                [InlineKeyboardButton(display_title, callback_data=f"lib|{key}")]
            )

    # 3. Botones de navegación (Subir nivel, Anterior, Siguiente)
    nav_buttons = []
    if st["historial"]:
        nav_buttons.append(
            InlineKeyboardButton("⬆️ Subir nivel", callback_data="subir_nivel")
        )
    if st["nav"]["prev"]:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="nav|prev"))
    if st["nav"]["next"]:
        nav_buttons.append(
            InlineKeyboardButton("➡️ Siguiente", callback_data="nav|next")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    if not st["historial"]:
        keyboard.append([InlineKeyboardButton("❌ Salir", callback_data="cerrar")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enviar o editar mensaje
    if new_message:
        # Si se pide mensaje nuevo, usar reply_text (o send_message)
        # Se asume que update tiene message o callback_query.message
        from utils.helpers import get_thread_id

        thread_id = get_thread_id(update)
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text=title,
            reply_markup=reply_markup,
            message_thread_id=thread_id,
        )
    elif hasattr(update, "message") and update.message:
        await update.message.reply_text(title, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(title, reply_markup=reply_markup)


async def buscar_zeepubs_directo(update, context, uid: int):
    """Acceso directo a ZeePubs [ES] detectándolo en el feed."""
    from core.state_manager import state_manager

    st = state_manager.get_user_state(uid)
    url = st.get("opds_root")
    logger.debug("Intentando acceso directo a ZeePubs desde %s", url)
    # Usar caché también aquí
    feed = await get_cached_feed(url)
    destino = find_zeepubs_destino(feed, prefer_libraries=True)
    if destino:
        st.update({"titulo": "📁 ZeePubs [ES]", "historial": []})
        await mostrar_colecciones(update, context, destino, from_collection=True)
    else:
        await mostrar_colecciones(update, context, url, from_collection=False)


async def get_zeepubs_first_library(url: str) -> str:
    """Obtiene la URL de la primera biblioteca dentro de ZeePubs [ES]."""
    # url es la raíz (OPDS_ROOT)
    feed = await get_cached_feed(url)
    libraries_url = find_zeepubs_destino(feed, prefer_libraries=True)

    # Ahora obtener la primera biblioteca dentro de /libraries
    lib_feed = await get_cached_feed(libraries_url)
    for entry in lib_feed.entries:
        for link in getattr(entry, "links", []):
            if getattr(link, "rel", "") == "subsection":
                return abs_url(config.BASE_URL, link.href)

    return libraries_url
