import uuid
import logging
from urllib.parse import urlparse, unquote
from difflib import SequenceMatcher
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
# from core.state_manager import state_manager (Moved to local scope)
from config.config_settings import config
from utils.http_client import parse_feed_from_url
from utils.helpers import abs_url, find_zeepubs_destino, extract_author, parse_metadata_from_title
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
        has_subsection = any(getattr(l, "rel", "") == "subsection" for l in getattr(entry, "links", []))
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

    # construir teclado
    keyboard = [[InlineKeyboardButton("🔍 Buscar EPUB", callback_data="buscar")]]

    if colecciones:
        for i, col in enumerate(colecciones):
            st["colecciones"][i] = col
            titulo_boton = col["titulo"]

            # Para no-admins, mostrar "Biblioteca ZeePubs" en lugar de "Todas las bibliotecas"
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
            st["libros"][key] = b
            
            # [NEW] Smart Format for Button Label
            # b["titulo"] comes from opds entry.title
            
            # Context Awareness: Get current folder title to avoid redundancy
            # Fallback to st["titulo"] (from previous nav) if feed.feed.title is missing
            feed_title = getattr(feed.feed, "title",  st.get("titulo", ""))
            
            # Clean common Kavita suffixes from context
            feed_title = feed_title.replace(" - Storyline", "")
            
            meta_context = parse_metadata_from_title(feed_title)
            context_series = meta_context.get("series", "").lower()
            
            meta = parse_metadata_from_title(b["titulo"])
            
            display_title = b["titulo"]
            if meta.get("series") and meta.get("volume"):
                # If we are inside the series folder (fuzzy match), show only volume
                book_series = meta["series"].lower()
                
                is_redundant = False
                if context_series and book_series:
                    # Remove non-alphanumeric to compare loosely
                    import re
                    s1 = re.sub(r"[^\w]", "", context_series)
                    s2 = re.sub(r"[^\w]", "", book_series)
                    
                    # 1. Direct Subset Match
                    if s1 in s2 or s2 in s1:
                        is_redundant = True
                    else:
                        # 2. Fuzzy Match (Ratio)
                        # Useful if one has extra subtitles but they share distinct series name
                        ratio = SequenceMatcher(None, s1, s2).ratio()
                        # If > 80% match, assume redundant
                        if ratio > 0.8:
                            is_redundant = True
                        else:
                            # 3. Common Prefix Match
                            # If they share a long prefix (e.g. > 15 chars), assume match
                            match = SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
                            if match.size > 15 and match.a == 0 and match.b == 0:
                                # Match starts at 0 for both (prefix match)
                                is_redundant = True

                # Determine minimal tags to show (tags in book but not in series context)
                book_tags = set(meta.get("tags", []))
                context_tags = set(meta_context.get("tags", []))
                unique_tags = sorted(list(book_tags - context_tags))
                
                tags_str = ""
                if unique_tags:
                    tags_str = " " + " ".join([f"[{t}]" for t in unique_tags])

                if is_redundant:
                    display_title = f"Volumen {meta['volume']}{tags_str}"
                else:
                    # Shorten format for buttons: "S. Name - Vol. 01 [Tags]"
                    # Truncate series if too long
                    s_name = meta["series"]
                    if len(s_name) > 20:
                        s_name = s_name[:17] + "..."
                    display_title = f"{s_name} - {meta['volume']}{tags_str}"
            elif meta.get("clean_title"):
                display_title = meta["clean_title"]

            keyboard.append([InlineKeyboardButton(display_title, callback_data=f"lib|{key}")])

    # Botones de navegación: todos en la misma fila
    nav_buttons = []

    # Botón "Subir nivel" (usar historial para ir al nivel anterior)
    if st["historial"]:
        nav_buttons.append(
            InlineKeyboardButton("⬆️ Subir nivel", callback_data="subir_nivel")
        )

    # Botones de paginación (navegar dentro de la misma biblioteca)
    if st["nav"]["prev"]:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="nav|prev"))
    if st["nav"]["next"]:
        nav_buttons.append(
            InlineKeyboardButton("➡️ Siguiente", callback_data="nav|next")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Botón Salir solo en el primer nivel (sin historial)
    if not st["historial"]:
        keyboard.append([InlineKeyboardButton("❌ Salir", callback_data="cerrar")])

    # Título y markup
    # Intento de mejorar el título si estamos en una vista de "Storyline" (Series de Kavita)
    title = st.get("titulo") or "📚 Categorías"
    
    # Lógica para extraer Romaji title si el feed title termina en " - Storyline"
    raw_feed_title = getattr(feed.feed, "title", "")
    if raw_feed_title.endswith(" - Storyline") and libros:
        # Intentar deducir la estructura English - Romaji - Volume del primer libro
        first_book_title = getattr(feed.entries[0], "title", "")
        clean_feed_title_part = raw_feed_title.replace(" - Storyline", "").strip()
        
        # Parseamos el primer libro para ver si contiene el título del feed + algo más en medio
        # Estructura esperada: "English Title [Tags] - Romaji Title - Volume info"
        # Ojo: parse_metadata_from_title limpia tags, así que usaremos split directo
        parts = first_book_title.split(" - ")
        
        if len(parts) >= 3:
            # Asumimos Part 0 = English (con tags), Part 1 = Romaji, Part 2+ = Info volumen
            # Verificamos si Part 0 coincide con el título del feed (aprox)
            
            # Limpieza básica para comparar (ignorar tags para la coincidencia base)
            import re
            def clean_title_part(s):
                # Remove tags
                s = re.sub(r"\[.*?\]", "", s)
                # Remove leading non-alphanumeric (bullets, etc), keeping parens if needed
                s = re.sub(r"^[^\w\(\)]+", "", s)
                return s.strip()

            p0_clean = clean_title_part(parts[0])
            feed_clean = clean_title_part(clean_feed_title_part)
            
            if p0_clean == feed_clean or p0_clean in feed_clean or feed_clean in p0_clean:
                # ¡Bingo! Tenemos un título Romaji potencial en parts[1]
                romaji_title = parts[1].strip()
                # Clean English title specifically to remove the bullet "⭘" if present
                english_title = re.sub(r"^[^\w\(\)]+", "", parts[0]).strip()
                
                # Construimos el nuevo título visual
                # Usamos el icono que ya pudiera tener el título del state o default
                icon_prefix = ""
                basic_title = title
                if " " in title:
                    # Intenta preservar el emoji inicial si existe (ej: 📁 )
                    possible_icon = title.split(" ", 1)[0]
                    # Validación simple de emoji (si no es alfanumérico)
                    if not possible_icon.isalnum():
                        icon_prefix = possible_icon + " "
                
                # Si st["titulo"] ya tenía el título en inglés, lo reemplazamos con el formato rico
                title = f"{icon_prefix}{english_title}\n\n{romaji_title}"

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
