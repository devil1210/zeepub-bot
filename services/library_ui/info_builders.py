# services/library_ui/info_builders.py
"""
Constructores de Bloques Nativos (Rich Messages) para Información, Ayuda, Donaciones y Reglas.
"""

from typing import Any


def build_status_rich_blocks(
    user_name: str,
    role_name: str = "",
    downloads_str: str = "",
    user_id: int | str = 0,
    joined_date: str = "",
    last_download_str: str = "",
    webapp_url: str = "",
    user_rank: str = "",
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Construye Bloques Nativos para la pantalla de Estado / Perfil."""
    effective_role = user_rank or role_name or "Lector"
    blocks: list[dict[str, Any]] = [
        {
            "type": "heading",
            "size": 2,
            "text": "👤 Perfil de Usuario • ZeePubs",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "👤 Nombre", "align": "left"},
                    {"text": user_name, "align": "left"},
                ],
                [
                    {"text": "⭐ Nivel / Rango", "align": "left"},
                    {"text": effective_role, "align": "left"},
                ],
                [
                    {"text": "📥 Cuota de Hoy", "align": "left"},
                    {"text": downloads_str, "align": "left"},
                ],
                [
                    {"text": "🆔 ID Telegram", "align": "left"},
                    {"text": str(user_id), "align": "left"},
                ],
                [
                    {"text": "📅 Miembro desde", "align": "left"},
                    {"text": str(joined_date), "align": "left"},
                ],
                [
                    {"text": "📚 Última Descarga", "align": "left"},
                    {"text": str(last_download_str), "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "💡 Accesos Rápidos",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• <b>/catalog</b> - Explorar catálogo completo\n• <b>/search &lt;título&gt;</b> - Buscar novelas\n• <b>/donar</b> - Conocer beneficios de niveles VIP y Premium",
                }
            ],
        },
    ]

    action_buttons = [
        {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
        {"text": "🏠 Inicio", "callback_data": "volver_menu"},
    ]
    if webapp_url:
        action_buttons.insert(0, {"text": "🌐 Abrir ZeePub Web", "url": webapp_url})

    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": action_buttons,
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #MiPerfil"})
    return blocks


def build_donations_rich_blocks(
    user_name: str,
    donation_url: str,
    p_white: str = "5",
    p_vip: str = "10",
    p_premium: str = "20",
    duration_months: str = "6",
) -> list[dict[str, Any]]:
    """Construye Bloques Nativos para Membresías, Niveles y Donaciones."""
    return [
        {
            "type": "heading",
            "size": 2,
            "text": "☕ Membresías y Donaciones • ZeePubs",
        },
        {
            "type": "paragraph",
            "text": [
                "¡Hola ",
                {"type": "bold", "text": user_name},
                "! Tu apoyo hace posible mantener los servidores, la maquetación y el desarrollo activo de nuevas funciones.",
            ],
        },
        {
            "type": "details",
            "summary": "⭐ Niveles y Beneficios Disponibles",
            "is_open": True,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_striped": True,
                    "is_compact": True,
                    "cells": [
                        [
                            {"text": "🤍 Whitelist", "align": "left"},
                            {"text": f"${p_white} USD", "align": "center"},
                            {"text": "10 descargas/día", "align": "left"},
                        ],
                        [
                            {"text": "⭐ VIP", "align": "left"},
                            {"text": f"${p_vip} USD", "align": "center"},
                            {"text": "Descargas Ilimitadas", "align": "left"},
                        ],
                        [
                            {"text": "💎 Premium", "align": "left"},
                            {"text": f"${p_premium} USD", "align": "center"},
                            {"text": "Ilimitadas + Prioridad", "align": "left"},
                        ],
                    ],
                },
                {
                    "type": "paragraph",
                    "text": f"<i>Beneficios válidos por <b>{duration_months} meses</b>.</i>",
                },
            ],
        },
        {
            "type": "details",
            "summary": "📝 ¿Cómo adquirir un nivel?",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "1. Pulsa en <b>Donar en Ko-fi</b> o usa <b>/stars</b>.\n2. En el mensaje de la donación, incluye tu ID o @usuario de Telegram.\n3. Tras donar, pulsa <b>Avisar al Staff</b> para activación inmediata.",
                }
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "☕ Donar en Ko-fi", "url": donation_url},
                {"text": "⭐ Donar con Stars", "callback_data": "stars_menu"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📩 Avisar al Staff", "callback_data": "notificar_donacion"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #Donaciones"},
    ]


def build_rules_rich_blocks() -> list[dict[str, Any]]:
    """Construye Bloques Nativos para las Reglas de la Comunidad."""
    return [
        {
            "type": "heading",
            "size": 2,
            "text": "📜 Normas de la Comunidad • ZeePubs",
        },
        {
            "type": "paragraph",
            "text": "Para mantener una convivencia sana y un espacio enfocado en la lectura, sigue estas normas:",
        },
        {
            "type": "details",
            "summary": "1. Respeto y Convivencia",
            "is_open": True,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• Trata con respeto a todos los miembros y al equipo de maquetación.\n• Prohibido insultos, discriminación, acoso o toxicidad.",
                }
            ],
        },
        {
            "type": "details",
            "summary": "2. Contenido Prohibido y Spam",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• Prohibido spam, flood, enlaces no autorizados o contenido NSFW/gore.",
                }
            ],
        },
        {
            "type": "details",
            "summary": "3. Uso Responsable del Bot",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• Respeta las cuotas de descarga diarias.\n• Usa <b>/search &lt;novela&gt;</b> en grupos para evitar mensajes innecesarios.",
                }
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #Reglas"},
    ]


def build_help_rich_blocks(user_rank: str = "Lector", is_staff: bool = False) -> list[dict[str, Any]]:
    """Construye Bloques Nativos para la Guía de Ayuda."""
    blocks: list[dict[str, Any]] = [
        {
            "type": "heading",
            "size": 2,
            "text": "📖 Guía de Uso y Comandos • ZeePubs",
        },
        {
            "type": "paragraph",
            "text": "Aprende a sacarle el máximo provecho a tu bot de lectura:",
        },
        {
            "type": "details",
            "summary": "🔍 Comandos Principales",
            "is_open": True,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• <b>/search &lt;título&gt;</b>: Búsqueda rápida por nombre, autor o categoría.\n• <b>/catalog</b>: Explora toda la biblioteca de novelas.\n• <b>/status</b>: Consulta tu cuota de descargas hoy y nivel de cuenta.\n• <b>/donar</b>: Información de membresías VIP y beneficios.\n• <b>/cancel</b>: Cancela cualquier acción en curso.",
                }
            ],
        },
    ]

    if is_staff:
        blocks.append(
            {
                "type": "details",
                "summary": "🛡️ Herramientas de Staff",
                "is_open": False,
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "• <b>/admin</b>: Panel de control con escáner, actualización y métricas.\n• <b>/stats</b>: Métricas de actividad y descargas.\n• <b>/id</b>: Ver información de identidad del chat.\n• <b>/setkey</b>: Actualizar API Key de Gemini en caliente.",
                    }
                ],
            }
        )

    blocks.extend([
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📖 Catálogo", "callback_data": "nav_local|all_series"},
                {"text": "🔍 Buscar", "callback_data": "buscar"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        },
        {"type": "divider"},
        {"type": "paragraph", "text": "#ZeePubs #Ayuda"},
    ])
    return blocks
