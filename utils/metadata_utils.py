import os
import re
from typing import Any

from utils.string_utils import normalize_author_name

SPANISH_ACCENTS_REGEX = re.compile(r"[áéíóúñüÁÉÍÓÚÑÜ¿¡]")

SPANISH_WORDS = {
    "el",
    "la",
    "los",
    "las",
    "un",
    "una",
    "unos",
    "unas",
    "del",
    "al",
    "en",
    "por",
    "para",
    "con",
    "sin",
    "sobre",
    "entre",
    "hacia",
    "hasta",
    "desde",
    "que",
    "como",
    "pero",
    "mas",
    "más",
    "muy",
    "mi",
    "tu",
    "su",
    "sus",
    "mis",
    "tus",
    "nuestro",
    "nuestra",
    "nuestros",
    "nuestras",
    "chico",
    "chica",
    "chicos",
    "chicas",
    "vida",
    "mundo",
    "paz",
    "siendo",
    "corriente",
    "solo",
    "sola",
    "me",
    "se",
    "te",
    "le",
    "les",
    "nos",
    "yo",
    "tu",
    "tú",
    "él",
    "ella",
    "ellos",
    "ellas",
    "novela",
    "ligera",
    "artes",
    "escenicas",
    "escénicas",
    "dejan",
    "deja",
    "dejaron",
    "princesa",
    "demonio",
    "reino",
    "magico",
    "mágico",
    "magia",
    "heroe",
    "héroe",
    "rey",
    "reina",
    "caballero",
    "mazmorra",
    "reencarnado",
    "reencarnada",
    "reencarnacion",
    "reencarnación",
    "otro",
    "otra",
    "otros",
    "otras",
    "cuando",
    "donde",
    "dónde",
    "quien",
    "quién",
    "porque",
    "por qué",
    "esto",
    "esta",
    "este",
    "estos",
    "estas",
    "aquel",
    "aquella",
    "todo",
    "toda",
    "todos",
    "todas",
}

DISTINCT_ROMAJI_WORDS = {
    "wa",
    "ga",
    "wo",
    "ni",
    "ka",
    "mo",
    "ya",
    "kara",
    "made",
    "san",
    "chan",
    "kun",
    "sama",
    "tonari",
    "desu",
    "kuro",
    "shiro",
    "boku",
    "ore",
    "watashi",
    "monogatari",
    "isekai",
    "tensei",
    "shinja",
    "kusuriya",
    "hitorigoto",
    "rosia",
    "russiago",
    "dereru",
    "bosotto",
    "arya",
    "yuusha",
    "maou",
    "konyakusha",
    "shoujo",
    "shounen",
    "seinen",
    "mahou",
    "ken",
    "tsukai",
    "tsundere",
    "gakuen",
    "senshi",
    "hime",
    "oujo",
    "kami",
    "tenshi",
    "akuma",
    "koushaku",
    "reijou",
    "otome",
    "harem",
    "yome",
    "kanojo",
    "dake",
    "haireru",
    "kakushi",
    "dungeon",
    "shikimori",
    "tomozaki",
    "danmachi",
    "rokudenashi",
    "konosuba",
    "rezero",
    "oregairu",
    "saekano",
    "toradora",
    "kokoro",
    "mushoku",
    "tenki",
    "koisuru",
    "astrea",
}


def is_spanish_string(text: str) -> bool:
    """Verifica si una cadena dada es predominantemente en Español."""
    if not text or not isinstance(text, str):
        return False
    if SPANISH_ACCENTS_REGEX.search(text):
        return True
    words = [w.lower() for w in re.findall(r"\b[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]+\b", text)]
    if not words:
        return False
    sp_matches = sum(1 for w in words if w in SPANISH_WORDS)
    if sp_matches >= 2:
        return True
    if len(words) >= 3 and (sp_matches / len(words)) >= 0.15:
        return True
    return False


def is_romaji_string(text: str) -> bool:
    """Verifica si una cadena dada es predominantemente Romaji / Japonés romanizado."""
    if not text or not isinstance(text, str):
        return False
    if is_spanish_string(text):
        return False
    if re.search(r"[\u3040-\u30ff\u4e00-\u9faf]", text):
        return True
    words = [w.lower() for w in re.findall(r"\b[a-zA-Z]+\b", text)]
    if not words:
        return False
    romaji_matches = sum(1 for w in words if w in DISTINCT_ROMAJI_WORDS)
    if "no" in words or "to" in words or "de" in words:
        if romaji_matches >= 1:
            return True
    return romaji_matches >= 2 or (
        len(words) >= 3 and (romaji_matches / len(words)) >= 0.25
    )


def resolve_title_cascade(data: dict[str, Any]) -> tuple[str, str | None, str | None]:
    """
    Resuelve de forma robusta la jerarquía de títulos:
    (title_en [🇬🇧], title_jp [🇯🇵], title_es [🇪🇸]).
    Garantiza que un título en español nunca se marque como japonés/romaji,
    y evita duplicaciones entre banderas.
    """
    t_en = (
        data.get("english_title")
        or data.get("series_english")
        or data.get("title")
        or data.get("titulo")
        or "Sin título"
    )
    t_jp = (
        data.get("romaji_title")
        or data.get("series_romaji")
        or data.get("series_name")
        or data.get("title_japanese")
        or data.get("title_jp")
        or data.get("romaji")
        or data.get("original_title")
    )
    t_es = (
        data.get("spanish_title")
        or data.get("title_spanish")
        or data.get("title_es")
        or data.get("series_spanish")
    )

    # 1. Si t_jp es en realidad español, reasignarlo a t_es
    if t_jp and is_spanish_string(t_jp):
        if not t_es or t_es == t_en:
            t_es = t_jp
        t_jp = None

    # 2. Si t_es es en realidad romaji o japonés, reasignarlo a t_jp
    if t_es and is_romaji_string(t_es):
        if not t_jp or t_jp == t_en:
            t_jp = t_es
        t_es = None

    # 3. Validar autenticidad de t_jp (debe ser romaji o japonés y distinto a t_en)
    if t_jp and (t_jp == t_en or not is_romaji_string(t_jp)):
        t_jp = None

    # 4. Descartar t_es si es idéntico a t_en
    if t_es and t_es == t_en:
        t_es = None

    return t_en, t_jp, t_es


def resolve_series_title(data: dict[str, Any], preference: str = "english") -> str:
    """
    Resuelve el título canónico para visualización de series/libros según la preferencia de idioma:
    - 'english' (por defecto oficial): name_english -> name (romaji) -> name_spanish
    - 'romaji': name (romaji) -> name_english -> name_spanish
    - 'spanish': name_spanish -> name_english -> name (romaji)
    """
    if not isinstance(data, dict):
        return str(data) if data else "Novela"

    t_en, t_jp, t_es = resolve_title_cascade(data)
    pref = (preference or "english").lower().strip()

    if pref == "spanish":
        return t_es or t_en or t_jp or "Novela"
    elif pref in ("romaji", "japanese", "jp"):
        return t_jp or t_en or t_es or "Novela"
    else:  # default "english"
        return t_en or t_jp or t_es or "Novela"


def clean_romaji_title(title: str) -> str:
    """
    Limpia un título en Romaji removiendo sufijos de volumen y grupos/corchetes finales.
    Ej: "Ore dake Haireru Kakushi Dungeon - Volumen 01 [GET]" -> "Ore dake Haireru Kakushi Dungeon"
    """
    if not title:
        return ""
    # Remover corchetes finales con cualquier tag
    clean = re.sub(r"\s*\[[^\]]+\]\s*$", "", title).strip()

    # Expresión regular robusta para remover el volumen y cualquier texto subsiguiente.
    # Cubre: - Volumen 01, - Vol. 04, - Vol 03, - Tomo 02, etc.
    volume_separator_pattern = re.compile(
        r"\s*[\-\–\—\−\―\~～\|¦║]?\s*(?:Volumen|Vol\.?|V|Tomo\.?|Parte|Part|Capítulo|Chapter)\s*\d+.*$",
        re.IGNORECASE,
    )
    clean = volume_separator_pattern.sub("", clean).strip()

    # Limpieza final de espacios repetidos
    return re.sub(r"\s+", " ", clean).strip()


def clean_english_title(title: str) -> str:
    """
    Limpia un título en inglés de indicadores de formato finales como [NL], [WN], [LN], [Manga].
    Ej: "The Hidden Dungeon Only I Can Enter [NL]" -> "The Hidden Dungeon Only I Can Enter"
    """
    if not title:
        return ""
    # Remover corchetes comunes al final que tengan las siglas de tipo de novela
    clean = re.sub(
        r"\s*\[(?:NL|WN|LN|Manga|WD|LN\s*Color|SC)\]\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()
    # Remover cualquier corchete final redundante
    clean = re.sub(r"\s*\[[^\]]+\]\s*$", "", clean).strip()
    return re.sub(r"\s+", " ", clean).strip()


def parse_metadata_from_title(
    title_str: str, preserve_special_chars: bool = False
) -> dict:
    """
    Parsea un título completo de forma inteligente.
    """
    if not title_str or not isinstance(title_str, str):
        return {"series": "", "volume": "", "clean_title": "", "tags": [], "romaji": ""}

    # Remover extensión .epub si está presente
    if title_str.lower().endswith(".epub"):
        title_str = title_str[:-5].strip()

    tags = re.findall(r"\[(.*?)\]", title_str)
    clean = re.sub(r"\[.*?\]", " ", title_str).strip()
    clean = re.sub(r"\(.*?\)", " ", clean).strip()

    # Separar por guiones, tildes, pipes, etc., SOLO si tienen espacios alrededor (para evitar cortar Sato-san)
    # Excepción para los dos puntos: solo separar si hay espacio alrededor o parece un subtítulo/volumen claro.
    # Evitamos separar "Re:Zero" o "Fate/stay"
    parts = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s+:\s+)", clean)

    volume = ""
    if len(parts) >= 2:
        volume_patterns = [
            r"^vol\.?\s*\d+",
            r"^v\s*\d+",
            r"^volume\s*\d+",
            r"^tomo\s*\d+",
            r"^part\s*\d+",
            r"^capítulo\s*\d+",
            r"^chapter\s*\d+",
            r"^\d+$",
        ]

        for i, part in enumerate(parts):
            if i == len(parts) - 1 and any(
                re.match(pattern, part.strip(), re.IGNORECASE)
                for pattern in volume_patterns
            ):
                volume = part.strip()
                parts = parts[:i]
                break

    romaji = ""
    if len(parts) >= 2 and not volume:
        p1 = parts[0].strip()
        p2 = parts[1].strip()

        if re.search(r"[ひらがなカ]", p2) or re.search(r"[a-zA-Z\s]+[ひらがなカ]", p2):
            romaji = p2
            series = p1
        elif any(
            part.lower() in ("no", "to", "ga", "wa", "ni", "de", "wo")
            for part in p2.split()
        ):
            # Detectar partículas Romaji comunes
            romaji = p2
            series = p1
        elif len(p1) < len(p2) * 0.8:
            romaji = p2
            series = p1
        else:
            series = p1
    else:
        series = " ".join(parts).strip()

    if not preserve_special_chars:
        # Solo limpiar caracteres basura al inicio/final que no sean parte del nombre.
        # No eliminar el colon ':' si está en medio.
        series = re.sub(r"^[^\w\(\)\[\]\:]+", "", series).strip()
        series = re.sub(
            r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\.\x23]+)$", "", series
        ).strip()

        if romaji:
            romaji = re.sub(r"^[^\w\(\)\[\]]+", "", romaji).strip()
            romaji = re.sub(
                r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.\x23]+)$", "", romaji
            ).strip()

    series_clean = re.sub(r"\s*\[.*?\]\s*", " ", series).strip()
    series_clean = re.sub(
        r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.]+)$", "", series_clean
    ).strip()

    # Limpiar mediante nuestras funciones de precisión
    if romaji:
        romaji = clean_romaji_title(romaji)
    series_clean = clean_romaji_title(series_clean)

    clean_title_result = series_clean if romaji else series_clean or clean
    clean_title_result = re.sub(r"\s+", " ", clean_title_result).strip()

    return {
        "series": series,
        "series_clean": series_clean,
        "volume": volume,
        "clean_title": clean_title_result,
        "tags": tags,
        "romaji": romaji,
    }


def generar_slug_from_meta(meta: Any) -> str:
    titulo_serie = None
    if isinstance(meta, dict):
        # El slug se calcula PRIORITARIAMENTE desde series_english según instrucciones del usuario
        titulo_serie = (
            meta.get("series_english")
            or meta.get("series_name")
            or meta.get("series")
            or meta.get("name")
            or meta.get("titulo_serie")
            or meta.get("series_clean")
            or meta.get("title")
        )
    elif isinstance(meta, str):
        titulo_serie = meta

    if not titulo_serie:
        return ""

    base_titulo = titulo_serie.strip()
    base_titulo = re.sub(r"\[.*?\]", "", base_titulo)

    parts = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s*:\s*)", base_titulo)
    if parts:
        first_part = parts[0].strip()
        if len(first_part) <= 3 and len(parts) > 1:
            base_titulo = first_part + " " + parts[1].strip()
        else:
            base_titulo = first_part

    base_titulo = base_titulo.replace("×", "x")
    base_titulo = base_titulo.replace(",", " ")

    # Reemplazar caracteres con tildes y ñ por sus equivalentes básicos
    import unicodedata

    base_titulo = "".join(
        c
        for c in unicodedata.normalize("NFD", base_titulo)
        if unicodedata.category(c) != "Mn"
    )
    # Solo permitir letras latinas básicas, números y espacios
    base_titulo = re.sub(r"[^a-zA-Z0-9\s_]", "", base_titulo)
    # Reemplazar múltiples espacios por uno solo
    base_titulo = re.sub(r"\s+", " ", base_titulo).strip()
    # Capitalizar inicial de cada palabra y unir con _
    words = re.split(r"[\s_]+", base_titulo)
    capitalized_words = [w.capitalize() for w in words if w]
    slug = "_".join(capitalized_words)
    return slug


DUMMY_PATTERNS = [
    r"^nombre\s+de\s+la\s+novela",
    r"^autor\s+apellido",
    r"^ilustrador\s+apellido",
    r"^grupo\s+traductor",
    r"^traductor$",
    r"^editorial$",
    r"^lorem\s+ipsum",
    r"^demograf[ií]a\d*",
    r"^g[eé]neroliterario\d*",
    r"^000-00-0000-000-0$",
    r"^bxxxxxxxx",
    r"^http://grupotraductor\.com",
    r"^siglas-grupo",
]


def is_dummy_value(val: Any) -> bool:
    """Detecta si un valor de metadatos es texto de relleno o plantilla genérica."""
    if val is None:
        return False
    if isinstance(val, (list, set, tuple)):
        return all(is_dummy_value(x) for x in val)
    val_str = str(val).strip().lower()
    if not val_str:
        return False
    for pat in DUMMY_PATTERNS:
        if re.search(pat, val_str, re.IGNORECASE):
            return True
    return False


def process_book_identity_comprehensive(
    epub_path: str = None,
    meta: dict | None = None,
    original_filename: str | None = None,
) -> dict:
    """
    Lógica UNIFICADA para extraer componentes de identidad de un EPUB.
    Si se provee 'meta', se evita re-extraer del EPUB.
    """
    if not meta:
        if not epub_path:
            return {}
        from utils.epub_extractor import EpubMetadataExtractor

        extractor = EpubMetadataExtractor(epub_path)
        meta = extractor.extract()

    if not meta:
        return {}

    # Limpiar placeholders y dummies del diccionario de metadatos OPF
    for k in ["title", "series", "author", "translator", "publisher", "illustrator", "description", "isbn", "asin", "author_jap", "illustrator_jap"]:
        if is_dummy_value(meta.get(k)):
            meta[k] = None

    # Metadata del EPUB: Origen sagrado de la Serie
    series_meta = meta.get("series")  # Tag específico de serie (Calibre/EPUB3)

    author = normalize_author_name(meta.get("author"))
    romaji_from_series = None
    series_spanish = meta.get("series_spanish")
    series_english = clean_english_title(series_meta) if series_meta else None

    # Filename parsing para título visual, tags, volumen y fallback de autor/serie
    parsed_filename = parse_metadata_from_title(original_filename)

    # Si el autor del OPF era placeholder o nulo, intentar extraer de carpeta contenedora
    if not author and epub_path:
        parent_dir = os.path.basename(os.path.dirname(epub_path))
        if parent_dir and " - " in parent_dir:
            dir_parts = [p.strip() for p in parent_dir.split(" - ") if p.strip()]
            if len(dir_parts) >= 2:
                author_cand = re.sub(r"\[.*?\]|\(.*?\)", "", dir_parts[1]).strip()
                if author_cand and not is_dummy_value(author_cand):
                    author = normalize_author_name(author_cand)

    if series_meta:
        # Solo intentar extraer partes si vienen con separadores claros tipo guiones o barras con espacios alrededor.
        parts = re.split(r"\s+[\-\–\—\−\―\~～\|¦║]\s+", series_meta)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) >= 3:
            if not series_spanish:
                series_spanish = parts[0]
            series_english = clean_english_title(parts[1])
            romaji_from_series = clean_romaji_title(parts[2])
            series = parts[0]
        elif len(parts) == 2:
            p1 = parts[0]
            p2 = parts[1]
            if (
                any(
                    part.lower() in ("no", "to", "ga", "wa", "ni", "de", "wo")
                    for part in p2.split()
                )
                or len(p1) < len(p2) * 0.8
            ):
                if not series_spanish:
                    series_spanish = p1
                romaji_from_series = clean_romaji_title(p2)
                series = p1
            else:
                if not series_spanish:
                    series_spanish = p1
                series_english = clean_english_title(p2)
                series = p1
        else:
            series_parsed_meta = parse_metadata_from_title(series_meta)
            series = (
                series_parsed_meta.get("series_clean")
                or series_parsed_meta.get("series")
                or series_meta
            )
            romaji_from_series = series_parsed_meta.get("romaji")
    else:
        # Si no hay tag de serie en el metadato, usar el del nombre del archivo
        series = parsed_filename.get("series_clean") or parsed_filename.get("series") or "Unknown"

    volume = meta.get("volume")
    translator = meta.get("translator")
    layout_by = meta.get("layout_by")
    language = meta.get("language") or "es"

    raw_tags = [t for t in meta.get("tags", []) if not is_dummy_value(t)]
    all_found_tags = list(raw_tags) + parsed_filename.get("tags", [])

    book_type = meta.get("book_type")
    if not book_type:
        for tag in all_found_tags:
            t_lower = tag.lower().strip()
            if t_lower in ["nl", "nw", "wn"]:
                book_type = {
                    "nl": "Novela Ligera",
                    "nw": "Novela Web",
                    "wn": "Novela Web",
                }[t_lower]
                break
            elif "novela" in t_lower:
                if "ligera" in t_lower:
                    book_type = "Novela Ligera"
                elif "web" in t_lower:
                    book_type = "Novela Web"
                else:
                    book_type = tag
                break

    # Título de visualización: Filename limpio (título en español) > dc:title
    ui_title = (
        parsed_filename.get("clean_title")
        or meta.get("title")
        or original_filename
        or "Sin título"
    )
    if ui_title.lower().endswith(".epub"):
        ui_title = ui_title[:-5].strip()
    romaji_from_title = parsed_filename.get("romaji")

    # Fallback para series_spanish si no viene de la serie OPF o si es Romaji
    if not series_spanish or is_romaji_string(series_spanish):
        fn_series = parsed_filename.get("series") or parsed_filename.get("clean_title")
        if fn_series and not is_romaji_string(fn_series):
            series_spanish = fn_series

    # Limpieza final de strings
    if series and series != "Unknown":
        series = clean_romaji_title(series)
    if romaji_from_series:
        romaji_from_series = clean_romaji_title(romaji_from_series)
    if romaji_from_title:
        romaji_from_title = clean_romaji_title(romaji_from_title)
    if series_english:
        series_english = clean_english_title(series_english)

    # Registro de Serie
    if series:
        series = series.strip()

    # Volumen: Extraer volumen del nombre del archivo
    fn_volume = None
    if parsed_filename.get("volume"):
        try:
            v_val = re.sub(r"[^\d.]", "", str(parsed_filename["volume"]))
            if v_val:
                fn_volume = float(v_val)
        except Exception:
            fn_volume = None

    # Prioridad: Si el metadato era nulo, o si el filename especifica un volumen (ej. V03 -> 3.0)
    # y el OPF tenía 1.0 (default de calibre) o era dummy, prevalece el filename.
    if volume is None:
        volume = fn_volume
    elif fn_volume is not None and volume == 1.0 and fn_volume != 1.0:
        volume = fn_volume

    if not book_type:
        book_type = "Light Novel"

    filename_to_check = original_filename or (
        os.path.basename(epub_path) if epub_path else ""
    )
    if filename_to_check:
        fname_lower = filename_to_check.lower()
        if meta.get("color_mode", "bw") == "bw":
            if any(
                x in fname_lower
                for x in ["[color]", "(color)", "[full color]", "color version"]
            ):
                meta["color_mode"] = "color"
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
        "author": author or "Unknown",
        "book_type": book_type,
        "volume": volume if volume is not None else 0.0,
        "translator": translator or "Unknown",
        "layout_by": layout_by or "Unknown",
        "language": language,
        "title": ui_title,
        "published_at": meta.get("published_at"),
        "edition": meta.get("edition"),
        "is_uncensored": meta.get("is_uncensored", 0),
        "color_mode": meta.get("color_mode", "bw"),
        "romaji_title": romaji_from_series
        or romaji_from_title
        or meta.get("romaji_title")
        or (
            clean_romaji_title(meta.get("title"))
            if (meta.get("title") and is_romaji_string(meta.get("title")))
            else None
        ),
        "series_spanish": series_spanish or meta.get("series_spanish"),
        "series_english": series_english or meta.get("series_english"),
        "uuid": meta.get("uuid"),
        "isbn": meta.get("isbn"),
        "asin": meta.get("asin"),
    }


async def get_series_spanish_from_api(
    series_name: str, author: str = None
) -> str | None:
    """
    Busca el título en español de una serie usando Google Books API.
    """
    import httpx

    try:
        from urllib.parse import quote

        query = quote(f'intitle:"{series_name}"')
        if author:
            query += quote(f' inauthor:"{author}"')

        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&langRestrict=es&maxResults=1"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)

        if response.status_code == 200:
            data = response.json()
            if data.get("totalItems", 0) > 0:
                item = data["items"][0]["volumeInfo"]
                return item.get("title")
    except Exception:
        pass
    return None


CANONICAL_DEMOGRAPHICS = ["Shounen", "Seinen", "Shoujo", "Josei", "Kodomo"]

DEMOGRAPHY_REGEX_MAP = [
    (
        "Shounen",
        re.compile(r"(?:^|[^\w])(?:shou?nen|shônen|chicos?)(?:$|[^\w])", re.IGNORECASE),
    ),
    (
        "Seinen",
        re.compile(
            r"(?:^|[^\w])(?:seinen|seijin|adultos?|mature)(?:$|[^\w])", re.IGNORECASE
        ),
    ),
    (
        "Shoujo",
        re.compile(r"(?:^|[^\w])(?:shou?jo|shôjo|chicas?)(?:$|[^\w])", re.IGNORECASE),
    ),
    ("Josei", re.compile(r"(?:^|[^\w])(?:josei|mujeres?)(?:$|[^\w])", re.IGNORECASE)),
    (
        "Kodomo",
        re.compile(
            r"(?:^|[^\w])(?:kodomo|niñ[oa]s?|nin[oa]s?|infantil|juvenil)(?:$|[^\w])",
            re.IGNORECASE,
        ),
    ),
]


def normalize_demography(val: Any) -> str:
    """
    Normaliza cualquier valor (string, objeto, lista) a una única demografía canónica:
    'Shounen', 'Seinen', 'Shoujo', 'Josei', 'Kodomo'.
    Si se detectan múltiples valores, selecciona solo la primera válida (evita concatenar múltiples demografías).
    """
    if not val:
        return ""

    items = val if isinstance(val, (list, set, tuple)) else [val]

    for item in items:
        if not item:
            continue
        name = getattr(item, "name", None) or str(item)
        name_clean = name.strip()
        if not name_clean:
            continue

        # 1. Coincidencia exacta con canonicals
        for canonical in CANONICAL_DEMOGRAPHICS:
            if name_clean.lower() == canonical.lower():
                return canonical

        # 2. Búsqueda por subcadena / regex (ej: "Chicos/shounen" -> "Shounen", "Adultos/Seinen" -> "Seinen")
        for canonical, pattern in DEMOGRAPHY_REGEX_MAP:
            if pattern.search(name_clean):
                return canonical

    return ""


def normalize_demographics_list(val: Any) -> list[str]:
    """
    Devuelve una lista con a lo sumo UNA demografía canónica normalizada.
    Ejemplo: ["Chicos/shounen", "Adultos/Seinen"] -> ["Shounen"]
    """
    demo = normalize_demography(val)
    return [demo] if demo else []


def is_demographic_tag(tag: str) -> bool:
    """Indica si un tag o subject corresponde a una demografía."""
    if not tag or not isinstance(tag, str):
        return False
    return bool(normalize_demography(tag.strip()))


def format_genre_chips(generos: Any, prefix: str = "#") -> str:
    """
    Convierte una lista o string de géneros en tags/chips estilizados.
    Ejemplo: ["Acción", "Ciencia Ficción"] -> "#Acción #Ciencia_Ficción"
    """
    if not generos:
        return ""
    if isinstance(generos, str):
        g_list = [g.strip() for g in re.split(r"[,;]+", generos) if g.strip()]
    elif isinstance(generos, (list, tuple, set)):
        g_list = [str(g).strip() for g in generos if str(g).strip()]
    else:
        return ""

    chips = []
    for g in g_list:
        clean_g = re.sub(r"[^\w\s]", "", g).strip().replace(" ", "_")
        if clean_g:
            chips.append(f"{prefix}{clean_g}")
    return " ".join(chips)
