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


def get_translator_acronym(translator: str | None) -> str:
    """Extrae las siglas de un traductor."""
    if not translator or translator == "Desconocido":
        return "?"

    # Si ya es corto (siglas existentes), devolverlo tal cual
    if len(translator) <= 5 and any(c.isupper() for c in translator):
        return translator

    # Limpiar tags y símbolos comunes
    name = re.sub(r"\[.*?\]", "", translator).strip()
    name = re.sub(r"\(.*?\)", "", name).strip()

    # Extraer letras iniciales de cada palabra
    parts = name.split()
    if not parts:
        return "?"

    acronym = "".join([p[0].upper() for p in parts if p and p[0].isalpha()])
    return acronym or "?"


def clean_caption_for_facebook(caption: str, public_link: str | None = None) -> str:
    """
    Formatea y limpia el texto para publicaciones de Facebook:
    - Elimina textos de ancla redundantes como 'Pulsa aquí', 'Pulsa aqui', 'Click aquí', dejando la URL limpia.
    - Convierte hipervínculos HTML (<a href="...">) y Markdown ([...](...)) a texto plano.
    - Preserva el formato limpio y respeta límites de caracteres de Facebook.
    """
    if not caption:
        caption = ""

    # 1. Reemplazar enlaces Markdown [anchor](url)
    def repl_md(match):
        anchor, url = match.group(1).strip(), match.group(2).strip()
        if not anchor or anchor.lower() in ("pulsa aquí", "pulsa aqui", "click aquí", "click aqui", "aquí", "aqui", "link", "descarga", "descargar"):
            return url
        return f"{anchor}: {url}"

    fb_caption = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', repl_md, caption)

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
