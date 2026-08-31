# services/library_ui/builders.py
"""
Fachada de Constructores Visuales (Rich Blocks / HTML).
Re-exporta constructores especializados desde `catalog_builders` y `book_builders`.
"""

from .admin_builders import (
    build_admin_panel_rich_blocks,
    build_admin_scan_result_blocks,
    build_auto_delete_menu_blocks,
)
from .book_builders import (
    build_book_rich_blocks,
    build_book_rich_html,
)
from .catalog_builders import (
    build_authors_rich_blocks,
    build_genres_rich_blocks,
    build_main_menu_rich_blocks,
    build_search_prompt_rich_blocks,
    build_search_results_rich_blocks,
    build_series_catalog_rich_blocks,
)
from .info_builders import (
    build_donations_rich_blocks,
    build_help_rich_blocks,
    build_rules_rich_blocks,
    build_status_rich_blocks,
)

__all__ = [
    # Catalog & Menu Builders
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
    "build_admin_panel_rich_blocks",
    "build_admin_scan_result_blocks",
    # Book & Series Builders
    "build_book_rich_blocks",
    "build_book_rich_html",
]
