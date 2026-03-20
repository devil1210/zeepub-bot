import os
import re
from typing import Any

from utils.epub_extractor import clean_metadata_tags
from utils.string_utils import normalize_author_name


def extract_spanish_series_from_filename(filename: str) -> str:
    """
    Extrae el nombre de la serie en español desde un nombre de archivo.
    Elimina - VXX, [Tags], extensiones y caracteres especiales.
    """
    if not filename:
        return ""

    # 1. Quitar extensión
    name = filename.rsplit(".", 1)[0]

    # 2. Quitar tags entre corchetes [TAG] e inclusive paréntesis (TAG)
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)

    # 3. Quitar patrón de volumen - VXX, VXX, etc.
    vol_pattern = r"(?:\s*[\-\–\—\−\―\:\~～\|¦]?\s*(?:Volumen|Vol\.?|Tomo|v\.?|V|Parte|#)\s*\d+(?:\.\d+)?.*)"
    name = re.sub(vol_pattern, "", name, flags=re.IGNORECASE).strip()

    # 4. Quitar subtítulos tras ~, |, ║ si los hay (requiere espacio alrededor para no dañar palabras)
    name = re.split(r"\s+[\~～\|¦║]\s+", name)[0].strip()

    # 5. Quitar guiones y símbolos al final/inicio
    name = re.sub(r"^[^\w\(\)\[\]]+", "", name).strip()
    name = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.\?\x23]+)$", "", name).strip()

    # 6. Limpiar espacios múltiples
    name = re.sub(r"\s+", " ", name).strip()

    return name


def parse_metadata_from_title(title_str: str, preserve_special_chars: bool = False) -> dict:
    """
    Parsea un título completo de forma inteligente.
    """
    if not title_str or not isinstance(title_str, str):
        return {"series": "", "volume": "", "clean_title": "", "tags": [], "romaji": ""}

    tags = re.findall(r"\[(.*?)\]", title_str)
    clean = re.sub(r"\[.*?\]", " ", title_str).strip()
    clean = re.sub(r"\(.*?\)", " ", clean).strip()

    # Separar por guiones, tildes, pipes, etc., SOLO si tienen espacios alrededor (para evitar cortar Sato-san)
    # Excepción para los dos puntos ': ' que a veces no tienen espacio antes.
    parts = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s*:\s*)", clean)

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
        elif len(p1) < len(p2) * 0.8:
            romaji = p2
            series = p1
        else:
            series = p1
    else:
        series = " ".join(parts).strip()

    if not preserve_special_chars:
        series = re.sub(r"^[^\w\(\)\[\]]+", "", series).strip()
        series = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.\x23]+)$", "", series).strip()

        if romaji:
            romaji = re.sub(r"^[^\w\(\)\[\]]+", "", romaji).strip()
            romaji = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.\x23]+)$", "", romaji).strip()

    series_clean = re.sub(r"\s*\[.*?\]\s*", " ", series).strip()
    series_clean = re.sub(r"(?:\s+[\-\–\—\−\―\~～\|¦║]+\s*|[\:\.]+)$", "", series_clean).strip()

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
        titulo_serie = (
            meta.get("series_name")
            or meta.get("series_english")
            or meta.get("series")
            or meta.get("series_spanish")
            or meta.get("titulo_serie")
            or meta.get("series_clean")
            or meta.get("english_title")
            or meta.get("title_raw")
            or meta.get("title_spanish")
            or meta.get("title_english")
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

    # Asegurar minúsculas
    base_titulo = base_titulo.lower()
    # Limpiar solo caracteres alfanuméricos y espacios
    base_titulo = base_titulo.strip()
    # Reemplazar caracteres con tildes y ñ por sus equivalentes básicos
    import unicodedata

    base_titulo = "".join(c for c in unicodedata.normalize("NFD", base_titulo) if unicodedata.category(c) != "Mn")
    # Solo permitir letras latinas básicas, números y espacios
    # Eliminamos cualquier carácter que no sea a-z, 0-9 o espacio
    base_titulo = re.sub(r"[^a-z0-9\s]", "", base_titulo)
    # Reemplazar múltiples espacios por uno solo
    base_titulo = re.sub(r"\s+", " ", base_titulo).strip()
    # Los espacios pasan a ser guiones bajos
    slug = base_titulo.replace(" ", "_")
    return slug


def process_book_identity_comprehensive(epub_path: str, original_filename: str | None = None) -> dict:
    """
    Lógica UNIFICADA para extraer componentes de identidad de un EPUB.
    """
    from utils.epub_extractor import EpubMetadataExtractor

    extractor = EpubMetadataExtractor(epub_path)
    meta = extractor.extract()

    if not meta:
        return {}

    title = meta.get("title") or original_filename or "Sin título"
    author_raw = meta.get("author") or ""
    author = normalize_author_name(author_raw)
    series_meta = meta.get("series")
    romaji_from_series = None

    if series_meta:
        series_parsed_meta = parse_metadata_from_title(series_meta)
        series = series_parsed_meta.get("series_clean") or series_parsed_meta.get("series") or series_meta
        romaji_from_series = series_parsed_meta.get("romaji")
    else:
        series = None

    volume = meta.get("volume")
    translator = meta.get("translator")
    layout_by = meta.get("layout_by")
    language = meta.get("language") or "es"

    series_spanish = ""
    if original_filename:
        series_spanish = extract_spanish_series_from_filename(original_filename)
    elif epub_path:
        series_spanish = extract_spanish_series_from_filename(os.path.basename(epub_path))

    parsed = parse_metadata_from_title(title)
    all_found_tags = list(meta.get("tags", [])) + parsed.get("tags", [])

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

    ui_title = parsed.get("clean_title") or clean_metadata_tags(title)
    if not series and parsed.get("series"):
        series = parsed["series"]

    if series:
        series = series.strip()
    if volume is None and parsed.get("volume"):
        try:
            volume = float(parsed["volume"])
        except Exception:
            volume = None

    filename_to_check = original_filename or (os.path.basename(epub_path) if epub_path else "")
    if filename_to_check:
        fname_lower = filename_to_check.lower()
        if meta.get("color_mode", "bw") == "bw":
            if any(x in fname_lower for x in ["[color]", "(color)", "[full color]", "color version"]):
                meta["color_mode"] = "color"
        if any(x in fname_lower for x in ["[b&n]", "[b&w]", "(b&n)", "(b&w)"]):
            meta["color_mode"] = "bw"
        if not meta.get("is_uncensored"):
            if any(x in fname_lower for x in ["[sin censura]", "[uncensored]", "[no censura]", "(uncensored)"]):
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
        "romaji_title": romaji_from_series or parsed.get("romaji"),
    }
