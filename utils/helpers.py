import re
import html
from urllib.parse import urljoin, urlparse
from config.config_settings import config


def extract_author(entry, is_folder=False) -> str:
    """Extrae el autor de una entrada OPDS de forma robusta."""
    author = None

    # 1. FIRST: Try entry.authors (list) - this captures multiple authors
    authors = (
        entry.get("authors", [])
        if hasattr(entry, "get")
        else getattr(entry, "authors", [])
    )

    if authors:
        author = " - ".join(
            [
                a.get("name", "") if hasattr(a, "get") else getattr(a, "name", "")
                for a in authors
                if (hasattr(a, "get") and a.get("name")) or hasattr(a, "name")
            ]
        )

    # 2. Fallback: Try entry.author directo (si es objeto, buscar .name)
    if not author:
        single_author = (
            entry.get("author") if hasattr(entry, "get") else getattr(entry, "author", None)
        )
        if hasattr(single_author, "name"):
            author = single_author.name
        elif isinstance(single_author, dict):
            author = single_author.get("name")
        elif isinstance(single_author, str) and single_author:
            author = single_author

    # 3. Intentar entry.author_detail
    if not author:
        detail = (
            entry.get("author_detail")
            if hasattr(entry, "get")
            else getattr(entry, "author_detail", None)
        )
        if detail:
            author = (
                detail.get("name")
                if hasattr(detail, "get")
                else getattr(detail, "name", None)
            )

    # 4. Intentar namespaces (dc:creator, dcterms:creator)
    if not author:
        if hasattr(entry, "get"):
            author = entry.get("dc_creator") or entry.get("dcterms_creator")
        else:
            author = getattr(entry, "dc_creator", None) or getattr(
                entry, "dcterms_creator", None
            )

    # 5. Fallback final
    if not author:
        author = "Colección" if is_folder else "Desconocido"

    return author


def get_thread_id(update) -> int:
    """
    Extrae el message_thread_id de un Update de Telegram.
    Retorna None si no hay thread_id (chat privado o grupo sin topics).
    """
    if not update:
        return None

    # Intentar desde message
    if hasattr(update, "message") and update.message:
        return getattr(update.message, "message_thread_id", None)

    # Intentar desde callback_query.message
    if hasattr(update, "callback_query") and update.callback_query:
        if hasattr(update.callback_query, "message") and update.callback_query.message:
            return getattr(update.callback_query.message, "message_thread_id", None)

    return None


def is_command_for_bot(update, bot_username: str) -> bool:
    """
    Verifica si un comando está dirigido a este bot específicamente.
    En grupos con múltiples bots, los comandos pueden ir dirigidos a un bot
    específico usando /comando@nombrebot

    Args:
        update: Update de Telegram
        bot_username: Username del bot (sin @)

    Returns:
        True si el comando es para este bot o no tiene bot específico (chat privado)
        False si el comando es para otro bot
    """
    if not update or not hasattr(update, "message") or not update.message:
        return True

    # En chats privados, siempre es para este bot
    if update.effective_chat.type == "private":
        return True

    # Verificar si el mensaje tiene entidades de comando
    if not update.message.entities:
        return True

    # Buscar la entidad de bot_command
    for entity in update.message.entities:
        if entity.type == "bot_command":
            # Extraer el texto del comando
            command_text = update.message.text[
                entity.offset : entity.offset + entity.length
            ]

            # Si el comando tiene @botusername, verificar que sea este bot
            if "@" in command_text:
                # Formato: /comando@botusername
                mentioned_bot = command_text.split("@")[1]
                return mentioned_bot.lower() == bot_username.lower()

            # Si no tiene @, acepta el comando (comportamiento por defecto)
            return True

    return True


def abs_url(base: str, href: str) -> str:
    return href if href.startswith("http") else urljoin(base, href)


def norm_string(s: str) -> str:
    return " ".join((s or "").split()).casefold()


def limpiar_html_basico(texto_html: str) -> str:
    if not texto_html:
        return ""
    texto_html = texto_html.replace("<br>", "\n").replace("<br/>", "\n")
    texto_limpio = re.sub(r"<.*?>", "", texto_html)
    return "\n".join(
        [ln.rstrip() for ln in texto_limpio.strip().splitlines() if ln.strip()]
    )


def build_search_url(query: str, uid: int = None, role: str = None) -> str:
    from core.state_manager import state_manager

    # Default to START
    root = config.OPDS_ROOT_START

    # If role is provided, use it for root determination
    if role:
        if role == "admin":
            root = config.OPDS_ROOT_EVIL
        else:
            root = config.OPDS_ROOT_START
    elif uid:
        # Fallback to legacy config check if role not provided
        is_admin = uid in config.ADMIN_USERS
        if is_admin:
            root = config.OPDS_ROOT_EVIL
        else:
            root = config.OPDS_ROOT_START

    if "/series" in root:
        root_series = root.split("?")[0]
    else:
        root_series = f"{root}/series"
    return f"{root_series}?query={query}"


def find_zeepubs_destino(feed, prefer_libraries: bool = False):
    import logging

    if not feed:
        logging.debug("find_zeepubs_destino: feed is None")
        return None
    entries = getattr(feed, "entries", [])
    logging.debug(
        "find_zeepubs_destino: feed title=%s entries=%d",
        getattr(feed, "feed", {}).get("title", None),
        len(entries),
    )

    def norm(s):
        return " ".join((s or "").split()).casefold()

    candidatos = []
    for entry in entries:
        title = getattr(entry, "title", "")
        logging.debug("find_zeepubs_destino: entry.title=%r", title)
        tnorm = norm(title)
        for link in getattr(entry, "links", []):
            rel = getattr(link, "rel", "")
            href = getattr(link, "href", "")
            logging.debug(" find link rel=%r href=%r (entry=%r)", rel, href, title)
            if rel == "subsection" and href:
                full = abs_url(config.BASE_URL, href)
                candidatos.append((title, full))
                if (
                    "zeepub" in tnorm
                    or "zeepubs" in tnorm
                    or tnorm == norm("ZeePubs [ES]")
                ):
                    logging.debug(
                        "find_zeepubs_destino: título coincide con 'zeepub(s)': %r -> %s",
                        title,
                        full,
                    )
                    return full
    if prefer_libraries:
        for title, href in candidatos:
            path = urlparse(href).path.lower()
            if "/libraries" in path or "/collections" in path or "/library" in path:
                logging.debug(
                    "find_zeepubs_destino: (prefer_libraries) href contains pattern, choosing %s (title=%r)",
                    href,
                    title,
                )
                return href
        for title, href in candidatos:
            if "bibliotec" in norm(title):
                logging.debug(
                    "find_zeepubs_destino: (prefer_libraries) title suggests 'biblioteca', choosing %s (title=%r)",
                    href,
                    title,
                )
                return href
    if len(candidatos) == 1:
        logging.debug(
            "find_zeepubs_destino: unique candidate, returning %s", candidatos[0][1]
        )
        return candidatos[0][1]
    logging.debug(
        "find_zeepubs_destino: no destination found (candidates=%s)",
        [c for _, c in candidatos],
    )
    return None


def generar_slug_from_meta(meta: dict) -> str:
    titulo_serie = None
    if isinstance(meta, dict):
        titulo_serie = meta.get("titulo_serie") or meta.get("titulo_volumen")
    elif isinstance(meta, str):
        titulo_serie = meta
    if not titulo_serie:
        return ""
    base_titulo = titulo_serie.split(":", 1)[0].strip()
    base_titulo = re.sub(r"\[.*?\]", "", base_titulo)
    base_titulo = base_titulo.split("-", 1)[0].strip()
    base_titulo = base_titulo.replace("×", "x")
    base_titulo = base_titulo.replace(",", " ")
    for ch in (
        "'",
        "’",
        "#",
        "・",
        "+",
        ".",
        "‘",
        "’",
        "“",
        "”",
        "（",
        "）",
        "、",
        "：",
        "？",
        "！",
        "；",
        "?",
        "-",
        "_",
    ):
        base_titulo = base_titulo.replace(ch, "")
    base_titulo = re.sub(r"\s+", " ", base_titulo).strip()
    slug = base_titulo.replace(" ", "_")
    return slug


def parse_metadata_from_title(title_str: str) -> dict:
    """ "
    Parsea un título completo de forma inteligente.
    Retorna diccionario con: series, volume, clean_title, tags, romaji.
    Ej: "⭘ 86 - EIGHTY-SIX [NL] - 86 ―Eitishikkusu― - Volumen 01 [TFP]" ->
        series="86 - EIGHTY-SIX [NL]", volume="01", tags=["NL", "TFP"], romaji="86 ―Eitishikkusu―"
    """
    if not title_str:
        return {"series": "", "volume": "", "clean_title": "", "tags": [], "romaji": ""}

    # 1. Extraer tags en corchetes [Tag]
    tags = re.findall(r"\[(.*?)\]", title_str)
    # Limpiar título inicial de corchetes de forma global
    clean = re.sub(r"\[.*?\]", "", title_str).strip()

    # 1b. Limpiar símbolos decorativos al inicio de forma muy agresiva
    # Maneja ○, ●, ⭘, • y varios tipos de guiones/puntos
    clean = re.sub(r"^[^\w\(\)\[\]]+", "", clean).strip()

    # 2. Extract volume first to facilitate title splitting
    # Handles: Volumen, Vol, Tomo, v. y números decimales
    vol_pattern = r"(?:Volumen|Vol\.?|Tomo|v\.?|V)\s*(\d+(?:\.\d+)?)"
    match = re.search(vol_pattern, clean, re.IGNORECASE)

    volume = ""
    clean_no_vol = clean
    if match:
        volume = match.group(1)
        full_vol_str = match.group(0)
        # Remove " - Volumen XX" or " Volumen XX" from the string to get the base title
        # regex handles various hyphen types: - (hyphen), – (en dash), — (em dash), − (minus)
        clean_no_vol = re.sub(rf"\s*[\-\–\—\−]?\s*{re.escape(full_vol_str)}.*", "", clean, flags=re.IGNORECASE).strip()

    # 3. Split parts by various hyphen types to find English vs Romaji
    # re handles various hyphen types: - (hyphen), – (en dash), — (em dash), − (minus), ― (horizontal bar)
    # REQUIRE spaces around hyphens to avoid splitting names like Arya-san
    parts = [p.strip() for p in re.split(r"\s+[\-\–\—\−\―]\s+", clean_no_vol) if p.strip()]

    romaji = ""
    series = clean_no_vol

    if len(parts) >= 2:
        # Avoid taking "Storyline" or "Libro" as romaji
        last_part = parts[-1]
        if last_part.lower() not in ["storyline", "libro"]:
            romaji = last_part
            series = " - ".join(parts[:-1]) if len(parts) > 2 else parts[0]
        elif len(parts) >= 3:
            romaji = parts[-2]
            series = " - ".join(parts[:-2]) if len(parts) > 3 else parts[0]

    # 4. Fallback for specific Romaji structures (Japanese characters)
    if not romaji:
        specific_romaji_pattern = r"\s+[\-\–\—\−]\s+([^-]+?[―‐—–\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+[^-]*?)\s+[\-\–\—\−]\s+"
        sr_match = re.search(specific_romaji_pattern, clean, re.IGNORECASE)
        if sr_match:
            romaji = sr_match.group(1).strip()
            series = clean.replace(sr_match.group(0), " - ").strip()
            series = re.sub(vol_pattern, "", series, flags=re.IGNORECASE).strip()

    # 5. Final cleaning of series title and romaji
    # Ensure no leading symbols or trailing punctuation reach the final fields
    series = re.sub(r"^[^\w\(\)\[\]]+", "", series).strip()
    series = re.sub(r"[\-:\s]+$", "", series).strip()
    
    if romaji:
        romaji = re.sub(r"^[^\w\(\)\[\]]+", "", romaji).strip()
        romaji = re.sub(r"[\-:\s]+$", "", romaji).strip()

    # If we have Romaji, cleanTitle should be the English Part (series)
    # This allows the frontend to show English as main title if romaji exists
    clean_title_result = series if romaji else clean_no_vol
    # Final cleaning of clean_title_result
    clean_title_result = re.sub(r"^[^\w\(\)\[\]]+", "", clean_title_result).strip()

    return {
        "series": series,
        "volume": volume,
        "clean_title": clean_title_result,
        "tags": tags,
        "romaji": romaji,
    }


def parse_title_string(title_str: str) -> tuple[str, str]:
    """
    DEPRECATED: Use parse_metadata_from_title instead.
    Mantener por compatibilidad inversa si algo lo usa.
    """
    res = parse_metadata_from_title(title_str)
    return res["series"], res["volume"]


def formatear_mensaje_portada(meta: dict, include_slug: bool = True) -> str:
    slug = generar_slug_from_meta(meta)
    lines = []

    # Nueva lógica si existen los campos específicos
    internal_title = meta.get("internal_title")
    collection_title = meta.get("titulo_serie")

    # Si no hay titulo_serie pero sí filename_title, usar filename_title como collection
    if not collection_title and meta.get("filename_title"):
        collection_title = meta.get("filename_title")

    # Limpiar collection_title: remover [...] y su contenido
    if collection_title:
        collection_title = re.sub(r"\[.*?\]", "", collection_title).strip()

    if internal_title and collection_title:
        full_title = meta.get("titulo_volumen") or ""
        series, volume = parse_title_string(full_title)

        # Si no se encontró volumen, usar el título completo como serie (o dejar vacío volumen)
        if not series:
            series = full_title

        # Colocar el slug en la misma línea del título (si se solicita)
        titulo_line = f"Epub de: {series} ║ {collection_title} ║ {internal_title}"
        lines.append(titulo_line)

        if volume:
            lines.append(volume)

        if slug and include_slug:
            lines.append(f"#{slug}")
    else:
        # Lógica antigua (fallback) — poner slug en la misma línea que el título
        titulo_vol = meta.get("titulo_volumen") or ""

        # Intentar limpiar el título fallback también
        series_fb, volume_fb = parse_title_string(titulo_vol)
        if not series_fb:
            series_fb = titulo_vol

        lines.append(series_fb)

        if volume_fb:
            lines.append(volume_fb)

        if slug and include_slug:
            lines.append(f"#{slug}")

    # Common metadata fields
    categoria = meta.get("categoria") or "Desconocida"
    generos = ", ".join(meta.get("generos") or []) or "Desconocido"
    demografia = ", ".join(meta.get("demografia") or []) or "Desconocida"
    autor = meta.get("autor") or (
        meta.get("autores")[0] if meta.get("autores") else "Desconocido"
    )
    ilustrador = meta.get("ilustrador") or "Desconocido"
    maqus = meta.get("maquetadores") or []
    if not maqus:
        maqu_line = "<b>Maquetado por:</b> #ZeePub"
    else:
        maqu_line = "<b>Maquetado por:</b> " + " ".join(
            f"#{m.replace(' ', '')}" for m in maqus
        )

    traduccion_parts = []
    if meta.get("traductor"):
        traduccion_parts.append(meta["traductor"])
    if meta.get("publisher"):
        traduccion_parts.append(meta["publisher"])
    if meta.get("publisher_url"):
        traduccion_parts.append(meta["publisher_url"])
    traduccion_line = ""
    if traduccion_parts:
        traduccion_line = "<b>Traducción:</b> " + " − ".join(traduccion_parts)

    # Un único separador vacío entre encabezado y metadatos
    lines.append("")
    lines.extend(
        [
            maqu_line,
            f"<b>Categoría:</b> {categoria}",
            f"<b>Demografía:</b> {demografia}",
            f"<b>Géneros:</b> {generos}",
            f"<b>Autor:</b> {autor}",
            f"<b>Ilustrador:</b> {ilustrador}",
        ]
    )

    if meta.get("fecha_publicacion"):
        lines.append(f"<b>Publicado:</b> {meta['fecha_publicacion']}")
    if traduccion_line:
        lines.append(traduccion_line)

    # Filter out None but keep empty strings (though lines shouldn't have None)
    return "\n".join(line for line in lines if line is not None)


def formatear_titulo_fb(meta: dict) -> str:
    """
    Genera el título formateado para Facebook (sin slug, sin hashtags).
    Replica la lógica de formatear_mensaje_portada para el título.
    """
    lines = []

    # Nueva lógica si existen los campos específicos
    internal_title = meta.get("internal_title")
    collection_title = meta.get("titulo_serie")

    # Limpiar collection_title: remover [...] y su contenido
    if collection_title:
        collection_title = re.sub(r"\[.*?\]", "", collection_title).strip()

    if internal_title and collection_title:
        full_title = meta.get("titulo_volumen") or ""
        series, volume = parse_title_string(full_title)

        # Si no se encontró volumen, usar el título completo como serie (o dejar vacío volumen)
        if not series:
            series = full_title

        lines.extend(
            [f"Epub de: {series} ║ {collection_title} ║ {internal_title}", volume]
        )
    else:
        # Lógica antigua (fallback)
        titulo_vol = meta.get("titulo_volumen") or ""
        lines.append(titulo_vol)

    return "\n".join(line for line in lines if line).strip()


def formatear_metadata_fb(meta: dict) -> str:
    """
    Genera el bloque de metadatos para Facebook (Maquetado, Categoría, etc.).
    """
    lines = []

    categoria = meta.get("categoria") or "Desconocida"
    generos = ", ".join(meta.get("generos") or []) or "Desconocido"
    demografia = ", ".join(meta.get("demografia") or []) or "Desconocida"
    autor = meta.get("autor") or (
        meta.get("autores")[0] if meta.get("autores") else "Desconocido"
    )
    ilustrador = meta.get("ilustrador") or "Desconocido"
    maqus = meta.get("maquetadores") or []

    if not maqus:
        maqu_line = "<b>Maquetado por:</b> #ZeePub"
    else:
        maqu_line = "<b>Maquetado por:</b> " + " ".join(
            f"#{m.replace(' ', '')}" for m in maqus
        )

    traduccion_parts = []
    if meta.get("traductor"):
        traduccion_parts.append(meta["traductor"])
    if meta.get("publisher"):
        traduccion_parts.append(meta["publisher"])
    if meta.get("publisher_url"):
        traduccion_parts.append(meta["publisher_url"])
    traduccion_line = ""
    if traduccion_parts:
        traduccion_line = "<b>Traducción:</b> " + " − ".join(traduccion_parts)

    lines.extend(
        [
            maqu_line,
            f"<b>Categoría:</b> {categoria}",
            f"<b>Demografía:</b> {demografia}",
            f"<b>Géneros:</b> {generos}",
            f"<b>Autor:</b> {autor}",
            f"<b>Ilustrador:</b> {ilustrador}",
        ]
    )

    if meta.get("fecha_publicacion"):
        lines.append(f"<b>Publicado:</b> {meta['fecha_publicacion']}")
    if traduccion_line:
        lines.append(traduccion_line)

    return "\n".join(line for line in lines if line)


def escapar_html(texto: str) -> str:
    return html.escape(texto) if texto else ""


def validate_facebook_credentials(config_obj) -> tuple[bool, str]:
    """
    Valida si las credenciales de Facebook están configuradas y no son placeholders.
    Retorna (True, "") si todo está bien.
    Retorna (False, mensaje_error) si falta algo o es inválido.
    """
    missing = []

    # Check Token
    token = config_obj.FACEBOOK_PAGE_ACCESS_TOKEN
    if not token or "your_token" in token or "token_falso" in token:
        missing.append("FACEBOOK_PAGE_ACCESS_TOKEN")

    # Check Group ID
    group_id = config_obj.FACEBOOK_GROUP_ID
    # "id_del_grupo" es el placeholder que causó el error 400
    if not group_id or "id_del_grupo" in group_id or "your_group_id" in group_id:
        missing.append("FACEBOOK_GROUP_ID")

    if missing:
        msg = (
            "⚠️ <b>Configuración inválida</b>\n\n"
            "No se puede publicar en Facebook porque las siguientes credenciales faltan o tienen valores por defecto (placeholders):\n"
            f"<code>{', '.join(missing)}</code>\n\n"
            "Por favor, ponte en contacto con un admin para que active el envío a Facebook."
        )
        return False, msg

    return True, ""


CURRENT_VERSION = "v5.0.31"


def get_current_version() -> str:
    return CURRENT_VERSION


def get_commit_hash() -> str:
    try:
        import os

        if os.path.exists("version_hash.txt"):
            with open("version_hash.txt", "r") as f:
                return f.read().strip()[:7]
    except Exception:
        pass
    return "unknown"


def get_version_string() -> str:
    v = get_current_version()
    h = get_commit_hash()
    if h and h != "unknown":
        return f"{v} ({h})"
    return v


def get_last_commit_message() -> str:
    """Obtiene el mensaje del último commit."""
    try:
        import subprocess

        # git log -1 --pretty=%B
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "Actualización desconocida"
