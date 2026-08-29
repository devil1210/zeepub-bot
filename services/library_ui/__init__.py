# services/library_ui/__init__.py
"""
Paquete modularizado de Interfaz de Usuario y Vistas para Telegram Rich Messages.
"""

from .builders import (
    build_authors_rich_blocks,
    build_book_rich_blocks,
    build_book_rich_html,
    build_donations_rich_blocks,
    build_genres_rich_blocks,
    build_help_rich_blocks,
    build_main_menu_rich_blocks,
    build_rules_rich_blocks,
    build_search_prompt_rich_blocks,
    build_search_results_rich_blocks,
    build_series_catalog_rich_blocks,
    build_status_rich_blocks,
)
from .catalog_views import (
    check_is_admin_or_staff,
    mostrar_autores_local,
    mostrar_generos,
    mostrar_libros,
    mostrar_menu_principal,
    mostrar_resultados_locales,
    mostrar_series,
    pedir_termino_busqueda,
)
from .series_views import (
    mostrar_detalles_libro,
    mostrar_volumenes_local,
)

__all__ = [
    # Builders
    "build_main_menu_rich_blocks",
    "build_genres_rich_blocks",
    "build_series_catalog_rich_blocks",
    "build_authors_rich_blocks",
    "build_search_prompt_rich_blocks",
    "build_search_results_rich_blocks",
    "build_status_rich_blocks",
    "build_donations_rich_blocks",
    "build_rules_rich_blocks",
    "build_help_rich_blocks",
    "build_book_rich_blocks",
    "build_book_rich_html",
    # Catalog Views
    "check_is_admin_or_staff",
    "mostrar_menu_principal",
    "mostrar_generos",
    "mostrar_series",
    "mostrar_libros",
    "mostrar_autores_local",
    "pedir_termino_busqueda",
    "mostrar_resultados_locales",
    # Series Views
    "mostrar_volumenes_local",
    "mostrar_detalles_libro",
]
