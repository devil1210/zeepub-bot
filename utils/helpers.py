import html
import os
import re
from typing import Any
from urllib.parse import urljoin

from utils.epub_extractor import clean_metadata_tags


def extract_creators_by_role(entry, role_code: str) -> str | None:
    """DESACTIVADO."""
    return None


def extract_author(entry, is_folder=False) -> str:
    """DESACTIVADO."""
    return "Desconocido"


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
            command_text = update.message.text[entity.offset : entity.offset + entity.length]

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


def norm_string(s: Any, lowercase: bool = True) -> str:
    if s is None:
        return ""
    text = str(s)
    # Remove content in square brackets [Tags]
    text = re.sub(r"\[.*?\]", "", text)
    # Remove content in parentheses (Jap Name / Extra Info)
    text = re.sub(r"\(.*?\)", "", text)
    # Normalize spaces
    res = " ".join(text.split()).strip()
    return res.casefold() if lowercase else res


def normalize_author_name(name: str) -> str:
    """
    Normaliza nombres de autores eliminando tags, limpiando espacios y estandarizando formato.
    Maneja (Apellido, Nombre -> Nombre Apellido) y elimina roles comunes.
    Preserva mayúsculas si existen, o aplica .title() si viene todo en minúsculas.
    """
    if not name:
        return ""

    # 1. Limpieza inicial SIN forzar minúsculas
    clean_name = norm_string(name, lowercase=False)

    # 2. Eliminar roles que a veces vienen sin paréntesis
    roles_to_remove = [
        "autor",
        "writer",
        "escritor",
        "story",
        "ilustrador",
        "illustrator",
        "art",
        "dibujo",
    ]
    for role in roles_to_remove:
        clean_name = re.sub(rf"\b{role}\b", "", clean_name, flags=re.IGNORECASE)

    # 3. Si detecta formato "Apellido, Nombre", invertir
    if "," in clean_name:
        parts = [p.strip() for p in clean_name.split(",")]
        if len(parts) == 2:
            clean_name = f"{parts[1]} {parts[0]}"

    # 4. Limpieza final de espacios múltiples
    clean_name = " ".join(clean_name.split()).strip()

    # 5. Si el nombre viene totalmente en minúsculas, aplicar Title Case
    if clean_name and clean_name.islower():
        clean_name = clean_name.title()

    return clean_name


def extract_spanish_series_from_filename(filename: str) -> str:
    """
    Extrae el nombre de la serie en español desde un nombre de archivo.
    Elimina - VXX, [Tags], extensiones y caracteres especiales.
    """
    if not filename:
        return ""

    # 1. Quitar extensión
    name = filename.rsplit(".", 1)[0]

    # 2. Quitar tags entre corchetes [TAG]
    name = re.sub(r"\[.*?\]", "", name)

    # 3. Quitar patrón de volumen - VXX, VXX, etc.
    vol_pattern = r"(?:\s*[\-\–\—\−]?\s*(?:Volumen|Vol\.?|Tomo|v\.?|V)\s*\d+(?:\.\d+)?.*)"
    name = re.sub(vol_pattern, "", name, flags=re.IGNORECASE).strip()

    # 4. Quitar subtítulos tras ~ o | si los hay (Normalización de serie)
    name = re.split(r"\s+[\~～\|¦]\s+", name)[0].strip()

    # 4. Quitar guiones y símbolos al final que puedan haber quedado
    name = re.sub(r"[\-\–\—\−\―\:\.\s]+$", "", name).strip()

    # 5. Limpiar espacios múltiples
    name = re.sub(r"\s+", " ", name).strip()

    return name


def process_book_identity_comprehensive(epub_path: str, original_filename: str | None = None) -> dict:
    """
    Lógica UNIFICADA para extraer componentes de identidad de un EPUB.
    Usada tanto por el Scanner como por el Uploader para garantizar paridad de hashes.
    """
    from utils.epub_extractor import EpubMetadataExtractor

    extractor = EpubMetadataExtractor(epub_path)
    meta = extractor.extract()

    if not meta:
        return {}

    title = meta.get("title") or original_filename or "Sin título"
    author = normalize_author_name(meta.get("author"))
    series_meta = meta.get("series")
    # Si la serie viene con subtítulos en la metadata (ej: "Serie ~ Subtítulo"), limpiarla
    if series_meta:
        series_parsed_meta = parse_metadata_from_title(series_meta)
        series = series_parsed_meta.get("series") or series_meta
    else:
        series = None
    volume = meta.get("volume")
    translator = meta.get("translator")
    layout_by = meta.get("layout_by")
    language = meta.get("language") or "es"

    # Extraer nombre de serie en español desde el nombre de archivo (Uploader o Scanner)
    series_spanish = ""
    if original_filename:
        series_spanish = extract_spanish_series_from_filename(original_filename)
    elif epub_path:
        series_spanish = extract_spanish_series_from_filename(os.path.basename(epub_path))

    # Categorización inteligente de tipos y extracción de metadata del título
    parsed = parse_metadata_from_title(title)
    all_found_tags = list(meta.get("tags", [])) + parsed.get("tags", [])

    book_type = meta.get("book_type")
    if not book_type:
        for tag in all_found_tags:
            t_lower = tag.lower().strip()
            if t_lower in ["nl", "nw", "wn"]:
                book_type = {
                    "nl": "Novela Ligera",
                    "nw": "Novela Web",
                    "wn": "Novela Web",  # Normalizar a Novela Web
                }[t_lower]
                break
            elif "novela" in t_lower:
                # Si el tag dice "Novela Ligera" o "Novela Web" directamente
                if "ligera" in t_lower:
                    book_type = "Novela Ligera"
                elif "web" in t_lower:
                    book_type = "Novela Web"
                else:
                    book_type = tag
                break

    # Limpiar el título para la UI (eliminar tags residuales)
    ui_title = parsed.get("clean_title") or clean_metadata_tags(title)
    if not series and parsed.get("series"):
        series = parsed["series"]

    # Normalización final de la serie para asegurar que no queden espacios extra o símbolos
    if series:
        series = series.strip()
    if volume is None and parsed.get("volume"):
        try:
            volume = float(parsed["volume"])
        except Exception:
            volume = None

    # --- ENRICHMENT FROM FILENAME ---
    # Detectar variantes de edición (Color, Censura) desde el nombre de archivo
    # si no vinieron en la metadata interna.
    filename_to_check = original_filename or (os.path.basename(epub_path) if epub_path else "")
    if filename_to_check:
        fname_lower = filename_to_check.lower()

        # 1. Color Mode detection
        if meta.get("color_mode", "bw") == "bw":  # Default in extractor is "bw", check if filename says otherwise
            if any(x in fname_lower for x in ["[color]", "(color)", "[full color]", "color version"]):
                meta["color_mode"] = "color"

        # If explicitly marked as B&W in filename, ensure it stays B&W (redundant but safe)
        if any(x in fname_lower for x in ["[b&n]", "[b&w]", "(b&n)", "(b&w)"]):
            meta["color_mode"] = "bw"

        # 2. Uncensored detection
        if not meta.get("is_uncensored"):
            if any(
                x in fname_lower
                for x in [
                    "[sin censura]",
                    "[uncensored]",
                    "[no censura]",
                    "(uncensored)",
                ]
            ):
                meta["is_uncensored"] = 1

    return {
        "series": series,
        "author": author,
        "book_type": book_type,
        "volume": volume,
        "translator": translator,
        "layout_by": layout_by,
        "language": language,
        "series_spanish": series_spanish,
        "series_english": parsed.get("series_clean") or series or series_spanish,
        "title": ui_title,
        "published_at": meta.get("published_at"),
        "edition": meta.get("edition"),
        "is_uncensored": meta.get("is_uncensored", 0),
        "color_mode": meta.get("color_mode", "bw"),
    }


def generate_book_hash(
    series: str | None = None,
    author: str | None = None,
    book_type: str | None = None,
    volume: Any | None = None,
    translator: str | None = None,
    layout_by: str | None = None,
    language: str | None = "es",
    edition: str | None = None,
    is_uncensored: int = 0,
    color_mode: str = "bw",
) -> str:
    """
    Genera un hash estable basado exclusivamente en: series + author + book_type + volume + translator + layout_by.
    NO usar title.
    """
    from services.hash_service import hash_service

    return hash_service.generate_book_hash(
        series=series,
        author=author,
        book_type=book_type,
        volume=volume,
        translator=translator,
        layout_by=layout_by,
        language=language,
        edition=edition,
        is_uncensored=is_uncensored,
        color_mode=color_mode,
    )


def generate_series_hash(series: str, author: str | None = None, book_type: str | None = None) -> str:
    """
    Genera un hash estable para la serie basado en: series + author + book_type.
    """
    from services.hash_service import hash_service

    return hash_service.generate_series_hash(series=series, author=author, book_type=book_type)


def limpiar_html_basico(texto_html: str) -> str:
    if not texto_html:
        return ""
    texto_html = texto_html.replace("<br>", "\n").replace("<br/>", "\n")
    texto_limpio = re.sub(r"<.*?>", "", texto_html)
    return "\n".join([ln.rstrip() for ln in texto_limpio.strip().splitlines() if ln.strip()])


def build_search_url(query: str, uid: int = None, role: str = None) -> str:
    """DESACTIVADO."""
    return ""


def find_zeepubs_destino(feed, prefer_libraries: bool = False):
    """DESACTIVADO."""
    return None


def generar_slug_from_meta(meta: dict) -> str:
    titulo_serie = None
    if isinstance(meta, dict):
        # PRIORIDAD: series o series_spanish (nombres principales/español)
        titulo_serie = (
            meta.get("series")
            or meta.get("series_spanish")
            or meta.get("series_english")
            or meta.get("titulo_serie")
            or meta.get("series_clean")
            or meta.get("english_title")
            or meta.get("title")
        )
    elif isinstance(meta, str):
        titulo_serie = meta
    if not titulo_serie:
        return ""
    base_titulo = titulo_serie.strip()
    base_titulo = re.sub(r"\[.*?\]", "", base_titulo)
    # Separar por guiones diversos, tildes, dos puntos o barras
    base_titulo = re.split(r"[\-\–\—\−\―\:\~\～\|¦]", base_titulo)[0].strip()
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
        "―",
        "—",
        "–",
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
        clean_no_vol = re.sub(
            rf"\s*[\-\–\—\−]?\s*{re.escape(full_vol_str)}.*",
            "",
            clean,
            flags=re.IGNORECASE,
        ).strip()

    # 3. Split parts by various hyphen types, colons, or dots to find English vs Romaji
    # re handles various hyphen types: - (hyphen), – (en dash), — (em dash), − (minus), ― (horizontal bar), ~ (tilde), ～ (full-width tilde)
    # Also support : and . as separators if followed by space, and | (pipe)
    # REQUIRE spaces around hyphens/colons/dots/tildes to avoid splitting names like Arya-san or St. Louis
    separators = r"\s+[\-\–\—\−\―\.\~～\|¦]\s+"
    parts = [p.strip() for p in re.split(separators, clean_no_vol) if p.strip()]

    romaji = ""
    series = clean_no_vol

    if len(parts) >= 2:
        # If we have exactly 2 parts, we need to decide which is English (series) and which is Romaji
        # Heuristic: The one with many non-ascii or Japanese characters is likely Romaji
        # Or if one is "Arifureta" and other is "From Commonplace...", the shorter one usually is Romaji
        p1, p2 = parts[0], parts[1]

        # Check for Japanese characters
        def has_jp(s):
            return bool(
                re.search(
                    r"[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\uFF00-\uFFEF]",
                    s,
                )
            )

        if has_jp(p2) and not has_jp(p1):
            romaji = p2
            series = p1
        elif has_jp(p1) and not has_jp(p2):
            romaji = p1
            series = p2
        else:
            # Fallback heuristic: the last part is often the Romaji subtitle in our library
            # UNLESS it's very long and the first part is short.
            # For "Arifureta: From ...", p1="Arifureta", p2="From Commonplace..."
            # Here "Arifureta" is Romaji.
            if len(p1) < len(p2) * 0.5:
                romaji = p1
                series = p2
            else:
                romaji = p2
                series = p1

    # 4. Special case for "Storyline" or "Libro"
    if romaji.lower() in ["storyline", "libro"] and len(parts) >= 3:
        romaji = parts[-2]
        series = " - ".join(parts[:-2])
    if not romaji:
        specific_romaji_pattern = (
            r"\s+[\-\–\—\−]\s+([^-]+?[―‐—–\u3000-\u303F\u3040-\u309F\u30A0-\u30FF]+[^-]*?)\s+[\-\–\—\−]\s+"
        )
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

    # REMOVE metadata brackets from series name for the "English Title" display
    # (e.g. "Series [NL]" -> "Series")
    series_clean = re.sub(r"\s*\[.*?\]\s*", " ", series).strip()
    # Also remove trailing punctuation if any remained after bracket removal
    series_clean = re.sub(r"[\-:\s]+$", "", series_clean).strip()

    # If we have Romaji, cleanTitle should be the English Part (series_clean)
    # This allows the frontend to show English as main title if romaji exists
    clean_title_result = series_clean if romaji else series_clean or clean_no_vol

    # Ensure no double spaces
    clean_title_result = re.sub(r"\s+", " ", clean_title_result).strip()

    return {
        "series": series,
        "series_clean": series_clean,  # New field for explicit clean English series
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


CURRENT_VERSION = "v7.1.1"


def get_current_version() -> str:
    return CURRENT_VERSION


def get_commit_hash() -> str:
    # 1. Try file (Watchtower/Production)
    try:
        import os

        if os.path.exists("version_hash.txt"):
            with open("version_hash.txt") as f:
                return f.read().strip()[:7]
    except Exception:
        pass

    # 2. Try Git
    try:
        import subprocess

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
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
