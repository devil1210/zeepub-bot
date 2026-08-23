import html
import re
from typing import Any


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


def limpiar_html_basico(texto_html: str) -> str:
    if not texto_html:
        return ""
    texto_html = texto_html.replace("<br>", "\n").replace("<br/>", "\n")
    texto_limpio = re.sub(r"<.*?>", "", texto_html)
    return "\n".join([ln.rstrip() for ln in texto_limpio.strip().splitlines() if ln.strip()])


def escapar_html(texto: str) -> str:
    return html.escape(texto) if texto else ""


def sanitize_fs_segment(name: str, fallback: str = "") -> str:
    """
    Limpia y sanitiza un nombre de archivo o carpeta individual para compatibilidad
    universal con todos los sistemas operativos (Windows, Linux, macOS, Android) y WebDAV/Nextcloud.

    Reglas:
    - Elimina caracteres prohibidos por SO y WebDAV: < > : " / \\ | ? * # % ^ y de control (0-31).
    - Para ':' lo reemplaza por '.' para preservar legibilidad en títulos tipo 'Re:Zero' -> 'Re.Zero'.
    - Elimina espacios y puntos finales o iniciales (prohibidos en Windows/Nextcloud).
    - Normaliza espacios múltiples.
    - Limita la longitud máxima a 150 caracteres.
    """
    if not name:
        return fallback

    s = str(name)
    # Reemplazar dos puntos por punto para títulos como Re:Zero -> Re.Zero
    s = s.replace(":", ".")
    # Eliminar caracteres de control (0-31)
    s = "".join(ch for ch in s if ord(ch) >= 32)
    # Eliminar caracteres prohibidos en Windows/Nextcloud/Linux: < > " / \ | ? * # % ^
    forbidden = r'[<>"/\\|?*#%^]'
    s = re.sub(forbidden, "", s)
    # Limpiar espacios múltiples
    s = re.sub(r"\s+", " ", s)
    # Eliminar espacios y puntos al inicio y al final
    s = s.strip(" .")
    return s[:150] or fallback


def sanitize_fs_path(path_str: str) -> str:
    """
    Sanitiza una ruta completa relativa (ej: 'Carpeta Serie/Volumen 01.epub'),
    asegurando que cada componente individual sea 100% compatible con todos los SO y Nextcloud.
    """
    if not path_str:
        return ""
    norm = str(path_str).replace("\\", "/").strip("/")
    parts = norm.split("/")
    clean_parts = []
    for p in parts:
        clean_p = sanitize_fs_segment(p)
        if clean_p:
            clean_parts.append(clean_p)
    return "/".join(clean_parts)


def get_translator_acronym(translator: str | None) -> str:
    """Extrae las siglas de un traductor sin caracteres prohibidos."""
    if not translator or translator in ("Desconocido", "Unknown", "?"):
        return "Unknown"

    # Si ya es corto (siglas existentes), limpiarlo y devolverlo
    cleaned_trans = sanitize_fs_segment(translator)
    if len(cleaned_trans) <= 5 and any(c.isupper() for c in cleaned_trans):
        return cleaned_trans

    # Limpiar tags y símbolos comunes
    name = re.sub(r"\[.*?\]", "", translator).strip()
    name = re.sub(r"\(.*?\)", "", name).strip()

    # Extraer letras iniciales de cada palabra
    parts = name.split()
    if not parts:
        return "Unknown"

    acronym = "".join([p[0].upper() for p in parts if p and p[0].isalnum()])
    return acronym or "Unknown"


def clean_caption_for_facebook(caption: str, public_link: str | None = None) -> str:
    """
    Formatea y limpia el texto para publicaciones de Facebook:
    - Elimina textos de ancla redundantes como 'Pulsa aquí', 'Pulsa aqui', 'Click aquí', dejando la URL limpia.
    - Convierte hipervínculos HTML (<a href="...">) y Markdown ([...](...)) a texto plano.
    - Preserva el formato limpio y respeta límites de caracteres de Facebook.
    """
    if not caption:
        caption = ""

    # 0. Decodificar entidades HTML (&lt; &gt; &amp; &quot; etc.)
    # El editor TipTap guarda el contenido con entidades escapadas que hay que revertir
    fb_caption = html.unescape(caption)

    # 1. Reemplazar enlaces Markdown [anchor](url)
    def repl_md(match):
        anchor, url = match.group(1).strip(), match.group(2).strip()
        if not anchor or anchor.lower() in ("pulsa aquí", "pulsa aqui", "click aquí", "click aqui", "aquí", "aqui", "link", "descarga", "descargar"):
            return url
        return f"{anchor}: {url}"

    fb_caption = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl_md, fb_caption)

    # 2. Reemplazar enlaces HTML <a href="url">anchor</a>
    def repl_html(match):
        url, anchor = match.group(1).strip(), match.group(2).strip()
        if not anchor or anchor.lower() in ("pulsa aquí", "pulsa aqui", "click aquí", "click aqui", "aquí", "aqui", "link", "descarga", "descargar"):
            return url
        return f"{anchor}: {url}"

    fb_caption = re.sub(r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', repl_html, fb_caption, flags=re.IGNORECASE)

    # 3. Limpiar saltos de línea HTML y etiquetas restantes
    fb_caption = re.sub(r'<(br|/p|/div|hr)\s*/?>', '\n', fb_caption, flags=re.IGNORECASE)
    fb_caption = re.sub(r'<p[^>]*>', '', fb_caption, flags=re.IGNORECASE)
    fb_caption = re.sub(r'<[^>]+>', '', fb_caption).strip()

    # 4. Eliminar "Pulsa aquí" si venía como texto plano previo ("Descarga: Pulsa aquí: https://...")
    fb_caption = re.sub(r'(Descarga:\s*)Pulsa aqu[íi]:?\s*', r'\1', fb_caption, flags=re.IGNORECASE)
    fb_caption = re.sub(r'Pulsa aqu[íi]:?\s*', '', fb_caption, flags=re.IGNORECASE)
    fb_caption = re.sub(r'Descarga:\s*:\s*', 'Descarga: ', fb_caption, flags=re.IGNORECASE)

    # 5. Añadir enlace público si existe y no está ya en la descripción
    if public_link and public_link not in fb_caption and "http" not in fb_caption:
        fb_caption = f"{fb_caption}\n\n⬇️ Descarga: {public_link}"

    # 6. Normalizar saltos de línea y longitud
    fb_caption = re.sub(r'\n{3,}', '\n\n', fb_caption)
    if len(fb_caption) > 2100:
        fb_caption = fb_caption[:2097] + "..."

    return fb_caption
