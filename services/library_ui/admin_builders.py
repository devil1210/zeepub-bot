# services/library_ui/admin_builders.py
"""
Constructores de Bloques Nativos (Rich Messages) para el Panel de Administración y Mantenimiento.
"""

from typing import Any


def build_admin_panel_rich_blocks(
    stats: dict[str, Any], git_hash: str = "v3.6.0", auto_del_mins: str = "2"
) -> list[dict[str, Any]]:
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
                    "text": f"⏱️ Auto-destrucción en grupos: <b>{auto_del_mins} min</b>\nSelecciona una acción a ejecutar:",
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
                {"text": "💾 Backup BD", "callback_data": "admin_act|backup"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🏢 Autorizar Grupo", "callback_data": "admin_act|toggle_group"},
                {"text": "⏱️ Auto-destrucción", "callback_data": "admin_act|timer_menu"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🧹 Integridad DB", "callback_data": "admin_act|integrity"},
                {"text": "📊 Estadísticas", "callback_data": "admin_act|stats"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🆔 Info Identidad", "callback_data": "admin_act|id"},
                {"text": "🏠 Volver al Inicio", "callback_data": "volver_menu"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #AdminPanel"},
    ]


def build_auto_delete_menu_blocks(current_mins: int = 2) -> list[dict[str, Any]]:
    """Construye el menú interactivo para seleccionar el tiempo de auto-destrucción en grupos."""
    presets = [1, 2, 3, 5, 10, 15]
    row1 = []
    row2 = []

    for m in presets[:3]:
        label = f"🔘 {m} min" if m == current_mins else f"{m} min"
        row1.append({"text": label, "callback_data": f"admin_set_timer|{m}"})

    for m in presets[3:]:
        label = f"🔘 {m} min" if m == current_mins else f"{m} min"
        row2.append({"text": label, "callback_data": f"admin_set_timer|{m}"})

    return [
        {
            "type": "heading",
            "size": 2,
            "text": "⏱️ Configurar Auto-destrucción en Grupos",
        },
        {
            "type": "paragraph",
            "text": (
                f"Configuración actual: <b>{current_mins} minutos</b>.\n\n"
                "<i>Selecciona cuántos minutos durarán los libros descargados en grupos NO autorizados antes de ser eliminados automáticamente:</i>"
            ),
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": row1,
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": row2,
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🛠️ Volver al Panel", "callback_data": "admin_panel"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #Configuracion"},
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
