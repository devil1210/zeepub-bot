# services/library_ui/book_builders.py
"""
Constructores de Bloques Nativos (Rich Blocks) y HTML para Fichas de Libros y Volúmenes de Serie.
"""

import logging
import re

from utils.helpers import (
    format_genre_chips,
    normalize_demography,
    resolve_title_cascade,
)

logger = logging.getLogger(__name__)


def build_book_rich_html(
    libro: dict,
    has_cover: bool = True,
    include_download: bool = False,
    filename: str | None = None,
    series_hash_short: str | None = None,
    collapsed: bool = False,
) -> str:
    """Construye el HTML dinámico completo para el Rich Message del libro."""
    html_parts = []

    if has_cover:
        html_parts.append('<img src="tg://photo?id=tomozaki_cover" />\n')

    title_en, title_jp, title_es = resolve_title_cascade(libro)
    html_parts.append(f"<h3>🇬🇧 {title_en}</h3>")
    if title_jp:
        html_parts.append(f"<h4>🇯🇵 {title_jp}</h4>")
    if title_es:
        html_parts.append(f"<h5>🇪🇸 {title_es}</h5>")

    volume = libro.get("volume")
    if volume:
        html_parts.append(f"<h6>📚 Volumen {volume}</h6>\n")

    generos = libro.get("tags_json") or libro.get("tags") or libro.get("generos")
    chips_generos = format_genre_chips(generos)
    if chips_generos:
        html_parts.append(f"<p>🏷️ <i>{chips_generos}</i></p>\n")

    tabla_open = "" if collapsed else " open"
    tabla_literaria = (
        f"<details{tabla_open}>\n"
        "  <summary>📋 Ficha Técnica</summary>\n"
        "  <table bordered striped compact>\n"
    )

    autor = libro.get("author") or libro.get("autor") or "Desconocido"
    tabla_literaria += f"    <tr><td><b>👤 Autor</b></td><td>{autor}</td></tr>\n"

    ilustrador = libro.get("illustrator") or libro.get("ilustrador")
    if ilustrador:
        ills = [
            i.strip()
            for i in re.split(r"[,;/+&]|\s+y\s+|\s+and\s+", str(ilustrador))
            if i.strip() and i.strip().upper() not in ("N/A", "DESCONOCIDO", "-")
        ]
        ill_val = ", ".join(ills) if len(ills) > 1 else str(ilustrador).strip()
        tabla_literaria += (
            f"    <tr><td><b>🎨 Ilustrador</b></td><td>{ill_val}</td></tr>\n"
        )

    layout_by = libro.get("layout_by") or libro.get("maquetador")
    if layout_by:
        maqs = [
            m.strip()
            for m in re.split(r"[,;]+|\s+(?=#)|\s+", str(layout_by))
            if m.strip()
        ]
        layout_val = " ".join(m if m.startswith("#") else f"#{m}" for m in maqs)
        tabla_literaria += (
            f"    <tr><td><b>💻 Maquetador</b></td><td>{layout_val}</td></tr>\n"
        )

    categoria = libro.get("book_type") or libro.get("tipo") or "Novela"
    tabla_literaria += f"    <tr><td><b>📦 Categoría</b></td><td>{categoria}</td></tr>\n"

    demo = (
        libro.get("demographics_json")
        or libro.get("demographics")
        or libro.get("demografia")
    )
    demo_val = normalize_demography(demo)
    if demo_val:
        tabla_literaria += (
            f"    <tr><td><b>👥 Demografía</b></td><td>{demo_val}</td></tr>\n"
        )

    traductor = libro.get("translator") or libro.get("traductor")
    if traductor:
        tabla_literaria += (
            f"    <tr><td><b>🌐 Traductor</b></td><td>{traductor}</td></tr>\n"
        )

    grupo_trad = (
        libro.get("publisher")
        or libro.get("translation_group")
        or libro.get("grupo_traductor")
    )
    if grupo_trad:
        grupo_trad_val = grupo_trad
        if libro.get("translation_group_url"):
            url_g = libro.get("translation_group_url")
            grupo_trad_val = f'<a href="{url_g}">{grupo_trad}</a>'
        tabla_literaria += (
            f"    <tr><td><b>🏢 Grupo Traductor</b></td><td>{grupo_trad_val}</td></tr>\n"
        )

    tabla_literaria += "  </table>\n</details>\n"
    html_parts.append(tabla_literaria)

    sinopsis_raw = libro.get("sinopsis") or "Sin sinopsis disponible."
    html_parts.append(
        "<details>\n"
        "  <summary>📖 Ver Sinopsis</summary>\n"
        "  <blockquote>\n"
        f"    {sinopsis_raw}\n"
        "  </blockquote>\n"
        "</details>\n"
    )

    size_val = libro.get("size")
    if not size_val and libro.get("file_size"):
        try:
            size_bytes = int(libro.get("file_size"))
            size_val = f"{size_bytes / (1024 * 1024):.2f} MB"
        except (ValueError, TypeError):
            size_val = "Desconocido"
    if not size_val:
        size_val = "Desconocido"

    version_val = libro.get("epub_version") or libro.get("version") or "3.0"

    tabla_archivo = (
        "<details>\n"
        "  <summary>📂 Ver Detalles del Archivo</summary>\n"
        "  <table bordered striped compact>\n"
        f"    <tr><td><b>📂 Nombre</b></td><td>{libro.get('title') or 'Desconocido'}</td></tr>\n"
    )
    if volume:
        tabla_archivo += (
            f"    <tr><td><b>📖 Volumen</b></td><td>Volumen {volume}</td></tr>\n"
        )

    tabla_archivo += (
        f"    <tr><td><b>ℹ️ Versión Epub</b></td><td>{version_val}</td></tr>\n"
    )

    fecha = (
        libro.get("updated_at") or libro.get("actualizado") or libro.get("indexed_at")
    )
    if fecha:
        if hasattr(fecha, "strftime"):
            fecha_str = fecha.strftime("%d-%m-%Y")
        else:
            fecha_str = str(fecha)
        tabla_archivo += (
            f"    <tr><td><b>📅 Actualizado</b></td><td>{fecha_str}</td></tr>\n"
        )

    tabla_archivo += f"    <tr><td><b>💾 Tamaño</b></td><td>{size_val}</td></tr>\n"
    tabla_archivo += "  </table>\n</details>\n"
    html_parts.append(tabla_archivo)

    if include_download:
        html_parts.append('  <tg-document src="tg://document?id=epub_file" />\n')

    html_parts.append("<hr/>")

    slug = libro.get("slug")
    if slug:
        hashtag_serie = slug if slug.startswith("#") else f"#{slug}"
    else:
        clean_title = re.sub(r"[^\w\s]", "", title_en).replace(" ", "_")
        hashtag_serie = f"#{clean_title}"

    html_parts.append(f"<p>{hashtag_serie}</p>")
    html_parts.append("<p>⠀</p>")

    return "\n".join(html_parts)


def html_to_rich_blocks_text(html_text: str) -> list | str:
    """
    Convierte una cadena HTML en una estructura de texto compatible con Telegram Bot API Rich Blocks:
    una lista compuesta por cadenas de texto plano y objetos estructurados como:
    {"type": "bold", "text": "..."} o {"type": "italic", "text": "..."}.
    """
    if not html_text:
        return ""

    s = str(html_text).strip()

    # 1. Normalizar artefactos markdown como > al inicio de citas o líneas
    s = re.sub(r"(<i>\s*)>\s*", r"\1", s, flags=re.IGNORECASE)
    s = re.sub(r"(^|\n)\s*>\s*", r"\1", s)

    # 2. Separar título inicial si viene pegado a <br>
    s = re.sub(r"</b>\s*(?:<br\s*/?>\s*)+", "</b>\n\n", s, flags=re.IGNORECASE)

    # 3. Agrupaciones de <br> (2 o más) representan cambio de párrafo limpio
    s = re.sub(r"(?:<br\s*/?>\s*){2,}", "\n\n", s, flags=re.IGNORECASE)

    # 4. <br> individual es un salto de línea simple dentro del mismo bloque (listas, autores, etc.)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)

    # 5. Etiquetas de párrafo <p>...</p>
    s = re.sub(r"</p>\s*<p[^>]*>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</?p[^>]*>", "\n", s, flags=re.IGNORECASE)

    # 6. Colapsar más de 2 saltos de línea consecutivos a exactamente 2 (\n\n)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()

    # Regex para extraer tags soportados: <b>, <strong>, <i>, <em>, <a>
    tag_pattern = r'<(b|strong|i|em|a)(?:\s+href=["\']([^"\']+)["\'])?>(.*?)</\1>'
    tag_re = re.compile(tag_pattern, re.IGNORECASE | re.DOTALL)

    result = []
    last_idx = 0

    def clean_text(t: str) -> str:
        t = re.sub(r"<[^>]+>", "", t)
        return (
            t.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )

    for match in tag_re.finditer(s):
        start_text = s[last_idx:match.start()]
        if start_text:
            cleaned_start = clean_text(start_text)
            if cleaned_start:
                result.append(cleaned_start)

        tag = match.group(1).lower()
        href = match.group(2)
        content = match.group(3)
        cleaned_content = clean_text(content)

        if cleaned_content:
            if tag in ("b", "strong"):
                result.append({"type": "bold", "text": cleaned_content})
            elif tag in ("i", "em"):
                result.append({"type": "italic", "text": cleaned_content})
            elif tag == "a" and href:
                result.append({"type": "url", "text": cleaned_content, "url": href})
            else:
                result.append(cleaned_content)

        last_idx = match.end()

    residual = s[last_idx:]
    if residual:
        cleaned_res = clean_text(residual)
        if cleaned_res:
            result.append(cleaned_res)

    if not result:
        return ""
    if len(result) == 1 and isinstance(result[0], str):
        return result[0]
    return result


def format_synopsis_rich_block(raw_synopsis: str | None) -> dict | None:
    """
    Normaliza el HTML de la sinopsis preservando negritas, cursivas y saltos de línea
    estructurados (evitando saltos dobles) y devuelve el bloque details/blockquote con
    la estructura de RichText nativa de Telegram Bot API.
    """
    if not raw_synopsis:
        return None

    rich_text = html_to_rich_blocks_text(raw_synopsis)
    if not rich_text:
        return None

    return {
        "type": "details",
        "summary": "📖 Ver Sinopsis",
        "is_open": False,
        "blocks": [
            {
                "type": "blockquote",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": rich_text,
                    }
                ],
            }
        ],
    }


def build_book_rich_blocks(
    libro: dict,
    has_cover: bool = True,
    cover_media: str = "attach://tomozaki_cover",
    key: str | None = None,
    can_download: bool = True,
    is_admin_or_staff: bool = False,
    include_download: bool = False,
    series_hash_short: str | None = None,
    volume_buttons: list[list[dict]] | None = None,
    show_nav_buttons: bool = False,
    collapsed: bool = False,
) -> list[dict]:
    """Construye la estructura de bloques nativos (Rich Blocks) para Telegram Bot API."""
    blocks = []

    if has_cover:
        blocks.append(
            {
                "type": "photo",
                "photo": {
                    "type": "photo",
                    "media": cover_media or "attach://tomozaki_cover",
                },
            }
        )

    title_en, title_jp, title_es = resolve_title_cascade(libro)
    blocks.append(
        {
            "type": "heading",
            "size": 3,
            "text": f"🇬🇧 {title_en}",
        }
    )
    if title_jp:
        blocks.append(
            {
                "type": "heading",
                "size": 4,
                "text": f"🇯🇵 {title_jp}",
            }
        )
    if title_es:
        blocks.append(
            {
                "type": "heading",
                "size": 5,
                "text": f"🇪🇸 {title_es}",
            }
        )

    volume = libro.get("volume")
    if volume:
        blocks.append(
            {
                "type": "heading",
                "size": 6,
                "text": f"📚 Volumen {volume}",
            }
        )

    generos = libro.get("tags_json") or libro.get("tags") or libro.get("generos")
    chips_generos = format_genre_chips(generos)
    if chips_generos:
        blocks.append(
            {
                "type": "paragraph",
                "text": f"🏷️ {chips_generos}",
            }
        )

    tabla_cells = []
    autor = libro.get("author") or libro.get("autor") or "Desconocido"
    tabla_cells.append([{"text": "👤 Autor"}, {"text": autor}])

    ilustrador = libro.get("illustrator") or libro.get("ilustrador")
    if ilustrador:
        ills = [
            i.strip()
            for i in re.split(r"[,;/+&]|\s+y\s+|\s+and\s+", str(ilustrador))
            if i.strip() and i.strip().upper() not in ("N/A", "DESCONOCIDO", "-")
        ]
        ill_val = ", ".join(ills) if len(ills) > 1 else str(ilustrador).strip()
        tabla_cells.append([{"text": "🎨 Ilustrador"}, {"text": ill_val}])

    layout_by = libro.get("layout_by") or libro.get("maquetador")
    if layout_by:
        maqs = [
            m.strip()
            for m in re.split(r"[,;/+&]|\s+y\s+|\s+and\s+", str(layout_by))
            if m.strip() and m.strip().upper() not in ("N/A", "DESCONOCIDO", "-")
        ]
        maq_tags = [m if m.startswith("#") else f"#{m}" for m in maqs]
        maq_val = (
            " ".join(maq_tags)
            if len(maq_tags) > 1
            else (maq_tags[0] if maq_tags else "")
        )
        if maq_val:
            tabla_cells.append([{"text": "📓 Maquetador"}, {"text": maq_val}])

    cat_val = libro.get("book_type") or libro.get("categoria") or "Novela Ligera"
    tabla_cells.append([{"text": "📦 Categoría"}, {"text": cat_val}])

    demografia = normalize_demography(
        libro.get("demographics") or libro.get("demografia")
    )
    if demografia:
        tabla_cells.append([{"text": "👥 Demografía"}, {"text": demografia}])

    traductor = libro.get("translator") or libro.get("traductor")
    if traductor:
        tabla_cells.append([{"text": "🌐 Traductor"}, {"text": str(traductor)}])

    grupo_tr = (
        libro.get("group") or libro.get("publisher") or libro.get("editorial")
    )
    if grupo_tr:
        tabla_cells.append([{"text": "🏢 Grupo Traductor"}, {"text": str(grupo_tr)}])

    blocks.append(
        {
            "type": "details",
            "summary": "📋 Ficha Técnica",
            "is_open": not collapsed,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_striped": True,
                    "is_compact": True,
                    "cells": tabla_cells,
                }
            ],
        }
    )

    # Sinopsis enriquecida con soporte completo de entidades y párrafos
    sinopsis_val = libro.get("sinopsis") or libro.get("description")
    sinopsis_block = format_synopsis_rich_block(sinopsis_val)
    if sinopsis_block:
        blocks.append(sinopsis_block)




    tech_cells = []
    formato = libro.get("epub_version") or "EPUB 3.0"
    tech_cells.append([{"text": "📄 Formato"}, {"text": formato}])

    raw_pages = libro.get("page_count")
    if raw_pages and str(raw_pages).isdigit() and int(raw_pages) > 0:
        tech_cells.append([{"text": "📑 Páginas"}, {"text": f"~{raw_pages} págs"}])

    raw_words = libro.get("word_count")
    if raw_words and str(raw_words).isdigit() and int(raw_words) > 0:
        tech_cells.append(
            [{"text": "📝 Palabras"}, {"text": f"{int(raw_words):,} palabras"}]
        )

    reading_time = libro.get("reading_time")
    if reading_time and str(reading_time).isdigit() and int(reading_time) > 0:
        mins = int(reading_time)
        hrs = mins // 60
        rem_mins = mins % 60
        time_str = f"{hrs}h {rem_mins}m" if hrs > 0 else f"{mins}m"
        tech_cells.append([{"text": "⏱️ Lectura"}, {"text": time_str}])

    fecha = (
        libro.get("modified_at_opf")
        or libro.get("published_at")
        or libro.get("modifiedAt")
        or libro.get("updated_at")
    )
    if fecha:
        if hasattr(fecha, "strftime"):
            fecha_str = fecha.strftime("%d-%m-%Y")
        else:
            fecha_str = str(fecha)
        tech_cells.append([{"text": "📅 Actualizado"}, {"text": fecha_str}])

    raw_size = libro.get("file_size") or libro.get("size")
    if raw_size:
        try:
            size_num = float(raw_size)
            if size_num >= 1024 * 1024:
                size_val = f"{size_num / (1024 * 1024):.1f} MB"
            elif size_num >= 1024:
                size_val = f"{size_num / 1024:.1f} KB"
            else:
                size_val = f"{int(size_num)} B"
        except (ValueError, TypeError):
            size_val = str(raw_size)
    else:
        size_val = "N/A"
    tech_cells.append([{"text": "💾 Tamaño"}, {"text": size_val}])

    blocks.append(
        {
            "type": "details",
            "summary": "📁 Ver Detalles del Archivo",
            "is_open": False,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_compact": True,
                    "cells": tech_cells,
                }
            ],
        }
    )

    if volume_buttons:
        for row in volume_buttons:
            if row:
                blocks.append(
                    {
                        "type": "buttons",
                        "align": "center",
                        "buttons": row,
                    }
                )

    if include_download:
        blocks.append(
            {
                "type": "document",
                "document": {
                    "type": "document",
                    "media": "attach://epub_file",
                },
            }
        )
    elif key:
        btn_text = (
            "📥 Descargar EPUB"
            if can_download
            else "⛔ Sin descargas disponibles"
        )
        cb_data = f"dl_confirm|{key}" if can_download else "noop"
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {
                        "text": btn_text,
                        "callback_data": cb_data,
                    }
                ],
            }
        )
        if is_admin_or_staff:
            blocks.append(
                {
                    "type": "buttons",
                    "align": "center",
                    "buttons": [
                        {
                            "text": "📢 Publicar en Telegram",
                            "callback_data": f"pub_channel|{key}",
                        }
                    ],
                }
            )

    if show_nav_buttons:
        nav_row = [
            {"text": "⬅️ Volver", "callback_data": "nav_back"},
            {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
            {"text": "🏠 Inicio", "callback_data": "main_menu"},
            {"text": "❌ Salir", "callback_data": "salir"},
        ]

        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": nav_row,
            }
        )

    blocks.append({"type": "divider"})
    slug = libro.get("slug")
    if slug:
        hashtag_serie = slug if slug.startswith("#") else f"#{slug}"
    else:
        clean_title = re.sub(r"[^\w\s]", "", title_en).replace(" ", "_")
        hashtag_serie = f"#{clean_title}"

    blocks.append({"type": "paragraph", "text": hashtag_serie})

    return blocks
