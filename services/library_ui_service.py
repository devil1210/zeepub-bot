# services/library_ui_service.py
"""
Fachada de Interfaz de Usuario para Telegram (ZeePub-bot v3.6+).
Re-exporta los módulos especializados del paquete `services.library_ui` manteniendo
compatibilidad retroactiva total con el resto del proyecto bajo la regla de <500 líneas.
"""

from services.cover_service import resolve_cover_data, send_photo_bytes
from services.library_ui import (
    build_admin_panel_rich_blocks,
    build_admin_scan_result_blocks,
    build_authors_rich_blocks,
    build_auto_delete_menu_blocks,
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
    cancel_nav_timer,
    check_is_admin_or_staff,
    ejecutar_admin_backup,
    ejecutar_admin_scan,
    ejecutar_admin_update,
    ejecutar_set_timer,
    ejecutar_toggle_grupo,
    is_nav_expired,
    mostrar_autores_local,
    mostrar_ayuda,
    mostrar_detalles_libro,
    mostrar_donaciones,
    mostrar_generos,
    mostrar_libros,
    mostrar_menu_principal,
    mostrar_menu_timer,
    mostrar_panel_admin,
    mostrar_reglas,
    mostrar_resultados_locales,
    mostrar_series,
    mostrar_volumenes_local,
    pedir_termino_busqueda,
    schedule_message_lifecycle,
)

__all__ = [
    # Portada Helpers
    "resolve_cover_data",
    "send_photo_bytes",
    # Rich Blocks Builders
    "build_main_menu_rich_blocks",
    "build_genres_rich_blocks",
    "build_series_catalog_rich_blocks",
    "build_authors_rich_blocks",
    "build_search_prompt_rich_blocks",
    "build_search_results_rich_blocks",
    "build_book_rich_blocks",
    "build_book_rich_html",
    "build_status_rich_blocks",
    "build_donations_rich_blocks",
    "build_rules_rich_blocks",
    "build_help_rich_blocks",
    "build_admin_panel_rich_blocks",
    "build_admin_scan_result_blocks",
    "build_auto_delete_menu_blocks",
    # Catalog & Info Views
    "check_is_admin_or_staff",
    "mostrar_menu_principal",
    "mostrar_generos",
    "mostrar_series",
    "mostrar_libros",
    "mostrar_autores_local",
    "pedir_termino_busqueda",
    "mostrar_resultados_locales",
    "mostrar_ayuda",
    "mostrar_donaciones",
    "mostrar_reglas",
    # Admin Views
    "mostrar_panel_admin",
    "ejecutar_admin_scan",
    "ejecutar_admin_update",
    "ejecutar_admin_backup",
    "ejecutar_toggle_grupo",
    "mostrar_menu_timer",
    "ejecutar_set_timer",
    # Series Views
    "mostrar_volumenes_local",
    "mostrar_detalles_libro",
    # Lifecycle
    "schedule_message_lifecycle",
    "is_nav_expired",
    "cancel_nav_timer",
]
