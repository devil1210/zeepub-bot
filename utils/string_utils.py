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
