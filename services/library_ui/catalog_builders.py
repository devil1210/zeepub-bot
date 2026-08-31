# services/library_ui/catalog_builders.py
"""
Constructores de Bloques Nativos (Rich Blocks) para Menú Principal, Géneros, Autores, Catálogo y Buscador.
"""

import logging
from typing import Optional

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


def build_search_prompt_rich_blocks(
    include_buttons: bool = True,
    searched_term: str | None = None,
) -> list[dict]:
    """Construye los bloques nativos para la pantalla de solicitud de búsqueda."""
    status_text = "Completada" if searched_term else "Esperando término..."
    inst_text = f'"{searched_term}"' if searched_term else "Escribe el texto en el chat"

    blocks = [
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
                [{"text": "🎯 Estado", "align": "left"}, {"text": status_text, "align": "left"}],
                [{"text": "✍️ Instrucción", "align": "left"}, {"text": inst_text, "align": "left"}],
            ],
        },
    ]

    if include_buttons:
        blocks.extend([
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
        ])

    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Buscador"})
    return blocks


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

