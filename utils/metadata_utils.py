import os
import re
from typing import Any

from utils.string_utils import normalize_author_name


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
        re.IGNORECASE
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
    clean = re.sub(r"\s*\[(?:NL|WN|LN|Manga|WD|LN\s*Color|SC)\]\s*$", "", title, flags=re.IGNORECASE).strip()
    # Remover cualquier corchete final redundante
    clean = re.sub(r"\s*\[[^\]]+\]\s*$", "", clean).strip()
    return re.sub(r"\s+", " ", clean).strip()


def parse_metadata_from_title(title_str: str, preserve_special_chars: bool = False) -> dict:
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
                re.match(pattern, part.strip(), re.IGNORECASE) for pattern in volume_patterns
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
        elif any(part.lower() in ("no", "to", "ga", "wa", "ni", "de", "wo") for part in p2.split()):
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
        series = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\.\x23]+)$", "", series).strip()

        if romaji:
            romaji = re.sub(r"^[^\w\(\)\[\]]+", "", romaji).strip()
            romaji = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.\x23]+)$", "", romaji).strip()

    series_clean = re.sub(r"\s*\[.*?\]\s*", " ", series).strip()
    series_clean = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.]+)$", "", series_clean).strip()

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
    base_titulo = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s*:\s*)", base_titulo)[0].strip()
    base_titulo = base_titulo.replace("×", "x")
    base_titulo = base_titulo.replace(",", " ")

    # Limpiar solo caracteres alfanuméricos y espacios
    base_titulo = base_titulo.strip()
    # Reemplazar caracteres con tildes y ñ por sus equivalentes básicos
    import unicodedata

    base_titulo = "".join(c for c in unicodedata.normalize("NFD", base_titulo) if unicodedata.category(c) != "Mn")
    # Solo permitir letras latinas básicas, números y espacios (luego se convertirán a _)
    # Eliminamos cualquier carácter que no sea a-z, A-Z, 0-9 o espacio
    base_titulo = re.sub(r"[^a-zA-Z0-9\s]", "", base_titulo)
    # Reemplazar múltiples espacios por uno solo
    base_titulo = re.sub(r"\s+", " ", base_titulo).strip()
    # Los espacios pasan a ser guiones bajos
    slug = base_titulo.replace(" ", "_")
    return slug


def process_book_identity_comprehensive(
    epub_path: str = None, meta: dict | None = None, original_filename: str | None = None
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

    # Metadata del EPUB: Origen sagrado de la Serie
    series_meta = meta.get("series")  # Tag específico de serie (Calibre/EPUB3)

    author = normalize_author_name(meta.get("author"))
    romaji_from_series = None
    series_spanish = None
    series_english = None

    if series_meta:
        # Intentar extraer partes si vienen con separadores en el tag de serie del EPUB
        parts = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s+:\s+)", series_meta)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 3:
            series_spanish = parts[0]
            series_english = clean_english_title(parts[1])
            romaji_from_series = clean_romaji_title(parts[2])
            series = parts[0]
        elif len(parts) == 2:
            p2 = parts[1]
            if any(part.lower() in ("no", "to", "ga", "wa", "ni", "de", "wo") for part in p2.split()) or len(parts[0]) < len(p2) * 0.8:
                series_spanish = parts[0]
                romaji_from_series = clean_romaji_title(p2)
                series = parts[0]
            else:
                series_spanish = parts[0]
                series_english = clean_english_title(p2)
                series = parts[0]
        else:
            series_parsed_meta = parse_metadata_from_title(series_meta)
            series = series_parsed_meta.get("series_clean") or series_parsed_meta.get("series") or series_meta
            romaji_from_series = series_parsed_meta.get("romaji")
    else:
        # Si no hay tag de serie en el metadato, NO usamos el título ni el nombre de archivo
        series = "Unknown"

    volume = meta.get("volume")
    translator = meta.get("translator")
    layout_by = meta.get("layout_by")
    language = meta.get("language") or "es"

    # El filename parsing se usa SOLO para el título visual y tags complementarios
    parsed_filename = parse_metadata_from_title(original_filename)
    all_found_tags = list(meta.get("tags", [])) + parsed_filename.get("tags", [])

    book_type = meta.get("book_type")
    if not book_type:
        for tag in all_found_tags:
            t_lower = tag.lower().strip()
            if t_lower in ["nl", "nw", "wn"]:
                book_type = {"nl": "Novela Ligera", "nw": "Novela Web", "wn": "Novela Web"}[t_lower]
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
    ui_title = parsed_filename.get("clean_title") or meta.get("title") or original_filename or "Sin título"
    if ui_title.lower().endswith(".epub"):
        ui_title = ui_title[:-5].strip()
    romaji_from_title = parsed_filename.get("romaji")

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

    # Volumen: Preferir metadato, fallback al filename solo si el metadato es nulo
    if volume is None and parsed_filename.get("volume"):
        try:
            v_val = re.sub(r"[^\d.]", "", str(parsed_filename["volume"]))
            if v_val:
                volume = float(v_val)
        except Exception:
            volume = None

    if not book_type:
        book_type = "Light Novel"

    filename_to_check = original_filename or (os.path.basename(epub_path) if epub_path else "")
    if filename_to_check:
        fname_lower = filename_to_check.lower()
        if meta.get("color_mode", "bw") == "bw":
            if any(x in fname_lower for x in ["[color]", "(color)", "[full color]", "color version"]):
                meta["color_mode"] = "color"
        if not meta.get("is_uncensored"):
            if any(x in fname_lower for x in ["[sin censura]", "[uncensored]", "[no censura]", "(uncensored)"]):
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
        "romaji_title": romaji_from_series or romaji_from_title or meta.get("romaji_title"),
        "series_spanish": series_spanish or meta.get("series_spanish"),
        "series_english": series_english or meta.get("series_english"),
    }


async def get_series_spanish_from_api(series_name: str, author: str = None) -> str | None:
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
