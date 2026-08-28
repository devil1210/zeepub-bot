# services/library_ui/builders.py
"""
Constructores puros de Bloques Nativos (Rich Blocks) y HTML para Telegram Rich Messages.
Responsabilidad única: Formateo, renderizado visual, tablas, acordeones y botones integrados.
"""

import io
import logging
import re
from typing import Optional

from utils.helpers import (
    format_genre_chips,
    normalize_demography,
    resolve_title_cascade,
)

logger = logging.getLogger(__name__)


def build_main_menu_rich_blocks(
    user_name: str,
    stats: dict,
    downloads_str: str,
    user_rank: str,
    webapp_url: str | None = None,
    show_webapp: bool = False,
) -> list[dict]:
    """Construye la estructura de bloques nativos (Rich Blocks) para el Menú Principal."""
    series_cnt = stats.get("series_count", 0)
    books_cnt = stats.get("books_count", 0)

    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": "🌟 ZeePubs • Biblioteca Digital",
        },
        {
            "type": "paragraph",
            "text": [
                "¡Hola, ",
                {"type": "bold", "text": user_name},
                "! Bienvenido a tu portal de lectura de Novelas Ligeras en formato EPUB maquetado.",
            ],
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "📚 Series Disponibles", "align": "left"},
                    {"text": f"{series_cnt} series", "align": "left"},
                ],
                [
                    {"text": "📖 Volúmenes Indexados", "align": "left"},
                    {"text": f"{books_cnt} libros", "align": "left"},
                ],
                [
                    {"text": "📥 Cuota de Hoy", "align": "left"},
                    {"text": downloads_str, "align": "left"},
                ],
                [
                    {"text": "👤 Rango", "align": "left"},
                    {"text": user_rank, "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "💡 Guía Rápida y Comandos",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• /search <título> - Buscar cualquier novela al instante\n• /catalogo - Ver todas las series de la colección\n• /menu o /start - Volver a este menú en cualquier momento",
                }
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📖 Catálogo de Series", "callback_data": "nav_local|all_series"},
                {"text": "⭐ Novedades", "callback_data": "nav_local|newest"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🏷️ Géneros", "callback_data": "nav_local|genres"},
                {"text": "✍️ Autores", "callback_data": "nav_local|authors"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🔍 Buscar Novela", "callback_data": "buscar"},
            ],
        },
    ]

    if show_webapp and webapp_url:
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "🌐 Abrir ZeePub Web", "url": webapp_url},
                    {"text": "❌ Salir", "callback_data": "salir"},
                ],
            }
        )
    else:
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "❌ Salir", "callback_data": "salir"},
                ],
            }
        )

    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #BibliotecaDigital"})

    return blocks


def build_genres_rich_blocks(genres: list[str]) -> list[dict]:
    """Construye los bloques nativos para el Explorador de Géneros."""
    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": "🏷️ Explorador de Géneros",
        },
        {
            "type": "paragraph",
            "text": "Selecciona una categoría para descubrir todas las novelas ligeras disponibles en la biblioteca:",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "🏷️ Total Categorías", "align": "left"},
                    {"text": f"{len(genres)} géneros", "align": "left"},
                ],
                [
                    {"text": "🎯 Modo de Exploración", "align": "left"},
                    {"text": "Filtrado directo por tag", "align": "left"},
                ],
            ],
        },
    ]

    for i in range(0, min(16, len(genres)), 2):
        row = [{"text": f"🏷️ {genres[i]}", "callback_data": f"gen|{genres[i]}"}]
        if i + 1 < len(genres):
            row.append(
                {"text": f"🏷️ {genres[i + 1]}", "callback_data": f"gen|{genres[i + 1]}"}
            )
        blocks.append({"type": "buttons", "align": "center", "buttons": row})

    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⬅️ Volver", "callback_data": "subir_nivel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Generos"})
    return blocks


def build_series_catalog_rich_blocks(
    title: str,
    items: list[dict],
    total_series: int,
    page: int,
    total_pages: int,
    origin_type: str,
    filter_val: str | None = None,
) -> list[dict]:
    """Construye los bloques nativos para el Catálogo de Series Paginado."""
    safe_filter = filter_val or ""
    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": title,
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "📚 Total Colección", "align": "left"},
                    {"text": f"{total_series} series", "align": "left"},
                ],
                [
                    {"text": "📄 Página Actual", "align": "left"},
                    {"text": f"{page} de {total_pages}", "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "📋 Series en esta página",
            "is_open": True,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_compact": True,
                    "cells": [
                        [
                            {"text": f"{i + 1}. {item.get('title', 'Novela')}", "align": "left"},
                            {"text": f"{item.get('book_count', 1)} vols", "align": "left"},
                        ]
                        for i, item in enumerate(items)
                    ]
                    if items
                    else [[{"text": "No se encontraron series en esta página", "align": "left"}]],
                }
            ],
        },
    ]

    for item in items:
        s_title = item.get("title", "Novela")
        idx = item.get("index", 0)
        if len(s_title) > 34:
            s_title = s_title[:31] + "..."
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [{"text": f"📁 {s_title}", "callback_data": f"col|{idx}"}],
            }
        )

    nav_row = []
    if page > 1:
        nav_row.append(
            {
                "text": "◀️ Ant.",
                "callback_data": f"nav_p|{origin_type}|{safe_filter}|{page - 1}",
            }
        )
    else:
        nav_row.append({"text": "⛔ 1", "callback_data": "noop"})

    nav_row.append(
        {"text": f"📄 {page}/{total_pages}", "callback_data": "noop"}
    )

    if page < total_pages:
        nav_row.append(
            {
                "text": "Sig. ▶️",
                "callback_data": f"nav_p|{origin_type}|{safe_filter}|{page + 1}",
            }
        )
    else:
        nav_row.append({"text": f"⛔ {total_pages}", "callback_data": "noop"})

    blocks.append({"type": "buttons", "align": "center", "buttons": nav_row})

    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⬅️ Volver", "callback_data": "subir_nivel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Catalogo"})
    return blocks


def build_authors_rich_blocks(
    authors: list[str],
    total_authors: int,
    page: int,
    total_pages: int,
) -> list[dict]:
    """Construye los bloques nativos para el Directorio de Autores."""
    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": "✍️ Directorio de Autores",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "✍️ Total Autores", "align": "left"},
                    {"text": f"{total_authors} autores", "align": "left"},
                ],
                [
                    {"text": "📄 Página Actual", "align": "left"},
                    {"text": f"{page} de {total_pages}", "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "📋 Autores en esta página",
            "is_open": True,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_compact": True,
                    "cells": [
                        [
                            {"text": f"{i + 1}. {a}", "align": "left"},
                            {"text": "Autor", "align": "left"},
                        ]
                        for i, a in enumerate(authors)
                    ]
                    if authors
                    else [[{"text": "No se encontraron autores en esta página", "align": "left"}]],
                }
            ],
        },
    ]

    for i in range(0, len(authors), 2):
        row = [{"text": f"✍️ {authors[i]}", "callback_data": f"aut|{authors[i]}"}]
        if i + 1 < len(authors):
            row.append(
                {"text": f"✍️ {authors[i + 1]}", "callback_data": f"aut|{authors[i + 1]}"}
            )
        blocks.append({"type": "buttons", "align": "center", "buttons": row})

    nav_row = []
    if page > 1:
        nav_row.append(
            {
                "text": "◀️ Ant.",
                "callback_data": f"nav_aut|{page - 1}",
            }
        )
    else:
        nav_row.append({"text": "⛔ 1", "callback_data": "noop"})

    nav_row.append(
        {"text": f"📄 {page}/{total_pages}", "callback_data": "noop"}
    )

    if page < total_pages:
        nav_row.append(
            {
                "text": "Sig. ▶️",
                "callback_data": f"nav_aut|{page + 1}",
            }
        )
    else:
        nav_row.append({"text": f"⛔ {total_pages}", "callback_data": "noop"})

    blocks.append({"type": "buttons", "align": "center", "buttons": nav_row})

    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⬅️ Volver", "callback_data": "subir_nivel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Autores"})
    return blocks


def build_search_prompt_rich_blocks() -> list[dict]:
    """Construye los bloques nativos para la pantalla de solicitud de búsqueda."""
    return [
        {
            "type": "heading",
            "size": 2,
            "text": "🔍 Búsqueda en la Biblioteca",
        },
        {
            "type": "paragraph",
            "text": "Encuentra cualquier novela ligera por su título (español, inglés o romaji), autor o categoría:",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [{"text": "🎯 Estado", "align": "left"}, {"text": "Esperando término...", "align": "left"}],
                [{"text": "✍️ Instrucción", "align": "left"}, {"text": "Escribe el texto en el chat", "align": "left"}],
            ],
        },
        {
            "type": "details",
            "summary": "💡 Consejos de Búsqueda",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• Escribe el nombre parcial: \"Mushoku\", \"Arifureta\", \"Tomozaki\"\n• O busca por autor: \"Rifujin\", \"Yaku\"\n• También puedes escribir directo: /search <término>",
                }
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📖 Catálogo Completo", "callback_data": "nav_local|all_series"},
                {"text": "🏷️ Explorar Géneros", "callback_data": "nav_local|genres"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Cancelar", "callback_data": "salir"},
            ],
        },
        {
            "type": "divider",
        },
        {
            "type": "paragraph",
            "text": "#ZeePubs #Buscador",
        },
    ]


def build_search_results_rich_blocks(
    query: str,
    series_results: list[dict],
    standalone_books: list[dict],
) -> list[dict]:
    """Construye los bloques nativos para la pantalla de resultados de búsqueda."""
    total_s = len(series_results)
    total_b = len(standalone_books)

    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": f"🔍 Resultados: \"{query}\"",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [{"text": "🎯 Término buscado", "align": "left"}, {"text": query, "align": "left"}],
                [{"text": "📁 Series encontradas", "align": "left"}, {"text": f"{total_s} series", "align": "left"}],
            ],
        },
    ]

    if total_s > 0 or total_b > 0:
        table_rows = []
        for s in series_results:
            name = s.get("name") or s.get("series_name") or s.get("title", "Serie")
            cnt = s.get("book_count") or 1
            table_rows.append([{"text": f"📁 {name}", "align": "left"}, {"text": f"{cnt} vols", "align": "left"}])
        for b in standalone_books:
            b_title = b.get("title", "Libro")
            table_rows.append([{"text": f"📕 {b_title}", "align": "left"}, {"text": "Individual", "align": "left"}])

        blocks.append(
            {
                "type": "details",
                "summary": "📋 Coincidencias Encontradas",
                "is_open": True,
                "blocks": [
                    {
                        "type": "table",
                        "is_bordered": True,
                        "is_compact": True,
                        "cells": table_rows if table_rows else [[{"text": "Sin resultados", "align": "left"}]],
                    }
                ],
            }
        )
    else:
        blocks.append(
            {
                "type": "paragraph",
                "text": f"❌ No se encontraron coincidencias para <b>{query}</b>.\nIntenta con un término más general o el nombre del autor.",
            }
        )

    for i, s in enumerate(series_results):
        name = s.get("name") or s.get("series_name") or s.get("title", "Serie")
        cnt = s.get("book_count") or 1
        btn_label = f"📁 {name}"
        if len(btn_label) > 30:
            btn_label = btn_label[:27] + "..."
        btn_label += f" ({cnt} vols)"
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [{"text": btn_label, "callback_data": f"col|{i}"}],
            }
        )

    for b in standalone_books:
        key = b.get("key")
        title = b.get("title", "Libro")
        if len(title) > 34:
            title = title[:31] + "..."
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [{"text": f"📕 {title}", "callback_data": f"lib|{key}"}],
            }
        )

    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🔍 Nueva Búsqueda", "callback_data": "buscar"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Resultados"})
    return blocks


def build_book_rich_html(
    libro: dict,
    has_cover: bool = True,
    include_download: bool = False,
    filename: str | None = None,
    series_hash_short: str | None = None,
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

    tabla_literaria = (
        "<details open>\n"
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
        except Exception:
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
        html_parts.append(
            "<details open>\n"
            "  <summary>📥 Descargar EPUB</summary>\n"
            '  <tg-document src="tg://document?id=epub_file" />\n'
            "</details>\n"
        )

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


def build_book_rich_blocks(
    libro: dict,
    has_cover: bool = True,
    include_download: bool = False,
    key: str | None = None,
    can_download: bool = True,
    is_admin_or_staff: bool = False,
    series_hash_short: str | None = None,
    volume_buttons: list[list[dict]] | None = None,
    show_nav_buttons: bool = True,
) -> list[dict]:
    """Construye la estructura de bloques nativos (Rich Blocks) para Telegram Bot API."""
    blocks = []

    if has_cover:
        blocks.append(
            {
                "type": "photo",
                "photo": {
                    "type": "photo",
                    "media": "attach://tomozaki_cover",
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
            "is_open": True,
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

    sinopsis = libro.get("sinopsis") or libro.get("description")
    if sinopsis:
        sinopsis_clean = re.sub(r"<[^>]+>", "", str(sinopsis)).strip()
        if len(sinopsis_clean) > 800:
            sinopsis_clean = sinopsis_clean[:790] + "..."
        blocks.append(
            {
                "type": "details",
                "summary": "📖 Ver Sinopsis",
                "is_open": False,
                "blocks": [
                    {
                        "type": "blockquote",
                        "blocks": [
                            {
                                "type": "paragraph",
                                "text": sinopsis_clean,
                            }
                        ],
                    }
                ],
            }
        )

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
                "type": "details",
                "summary": "📥 Descargar EPUB",
                "is_open": True,
                "blocks": [
                    {
                        "type": "document",
                        "document": {
                            "type": "document",
                            "media": "attach://epub_file",
                        },
                    }
                ],
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
