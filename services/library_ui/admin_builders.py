# services/library_ui/admin_builders.py
"""
Constructores de Bloques Nativos (Rich Messages) para el Panel de Administración y Mantenimiento.
"""

from typing import Any


def build_admin_panel_rich_blocks(stats: dict[str, Any], git_hash: str = "v3.6.0") -> list[dict[str, Any]]:
    """Construye Bloques Nativos para el Panel de Control de Administración."""
    series_cnt = stats.get("series_count", 0)
    books_cnt = stats.get("books_count", 0)
    users_cnt = stats.get("users_count", 0)

    return [
        {
            "type": "heading",
            "size": 2,
            "text": "🛠️ Panel de Control • ZeePubs Admin",
        },
        {
            "type": "paragraph",
            "text": "Bienvenido al centro de mantenimiento y administración de la biblioteca.",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "📦 Total Series", "align": "left"},
                    {"text": f"{series_cnt} series", "align": "left"},
                ],
                [
                    {"text": "📖 Total Libros", "align": "left"},
                    {"text": f"{books_cnt} libros", "align": "left"},
                ],
                [
                    {"text": "👥 Usuarios Registrados", "align": "left"},
                    {"text": f"{users_cnt} usuarios", "align": "left"},
                ],
                [
                    {"text": "🏷️ Versión Git", "align": "left"},
                    {"text": str(git_hash[:10]), "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "⚙️ Operaciones de Mantenimiento",
            "is_open": True,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "Selecciona una acción para ejecutar en la biblioteca:",
                }
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⚡ Escaneo Rápido", "callback_data": "admin_act|scan_soft"},
                {"text": "🔥 Escaneo Profundo", "callback_data": "admin_act|scan_full"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🚀 Actualizar Bot", "callback_data": "admin_act|update"},
                {"text": "🧹 Integridad DB", "callback_data": "admin_act|integrity"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📊 Estadísticas", "callback_data": "admin_act|stats"},
                {"text": "🆔 Info Identidad", "callback_data": "admin_act|id"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🏠 Volver al Inicio", "callback_data": "volver_menu"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #AdminPanel"},
    ]


def build_admin_scan_result_blocks(results: dict[str, Any]) -> list[dict[str, Any]]:
    """Construye Bloques Nativos con el resumen de escaneo de la biblioteca."""
    total_scanned = results.get("total_scanned", 0)
    added = results.get("added", 0)
    updated = results.get("updated", 0)
    duplicates = results.get("duplicates", 0)
    removed = results.get("removed", 0)
    sources = results.get("sources_scanned", 0)

    return [
        {
            "type": "heading",
            "size": 2,
            "text": "✅ Escaneo Completado • ZeePubs",
        },
        {
            "type": "paragraph",
            "text": "El escáner de la biblioteca local ha terminado de procesar los archivos EPUB:",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [{"text": "📚 Total Escaneados", "align": "left"}, {"text": str(total_scanned), "align": "right"}],
                [{"text": "✨ Nuevos Añadidos", "align": "left"}, {"text": str(added), "align": "right"}],
                [{"text": "📝 Actualizados", "align": "left"}, {"text": str(updated), "align": "right"}],
                [{"text": "📕 Duplicados", "align": "left"}, {"text": str(duplicates), "align": "right"}],
                [{"text": "🧹 Eliminados", "align": "left"}, {"text": str(removed), "align": "right"}],
                [{"text": "📂 Carpetas Fuente", "align": "left"}, {"text": str(sources), "align": "right"}],
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🛠️ Panel Admin", "callback_data": "admin_panel"},
                {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #Scanner"},
    ]
