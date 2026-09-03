# services/keyboard_factory.py
"""
Factory de Teclados Interactivos para Telegram (ZeePub-bot v3.6+).
Implementa estilos de botones nativos de Telegram Bot API 7.0+ (style: primary, success, danger),
soporte para custom emoji IDs animados, semiótica visual estricta y arquitectura Zero Dead-Ends.
"""

from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class BotKeyboards:
    """Constructor centralizado de teclados interactivos con estilos nativos y semiótica cromática."""

    @staticmethod
    def btn(
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
        style: Optional[
            str
        ] = None,  # "primary" (azul) | "success" (verde) | "danger" (rojo)
        icon_custom_emoji_id: Optional[str] = None,
        disabled: bool = False,
    ) -> InlineKeyboardButton:
        """
        Construye un InlineKeyboardButton con soporte nativo para estilos de color, premium emojis y estado disabled.
        Compatible con Telegram Bot API 7.0+ y 10.3.
        """
        api_kwargs = {}
        if style:
            api_kwargs["style"] = style
        if icon_custom_emoji_id:
            api_kwargs["icon_custom_emoji_id"] = str(icon_custom_emoji_id)
        if disabled:
            api_kwargs["disabled"] = True

        if api_kwargs:
            return InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
                url=url,
                api_kwargs=api_kwargs,
            )
        return InlineKeyboardButton(text=text, callback_data=callback_data, url=url)

    # ---------------------------------------------------------
    # 🏠 MENÚ PRINCIPAL
    # ---------------------------------------------------------
    @staticmethod
    def main_menu(
        webapp_url: str | None = None, show_webapp: bool = False
    ) -> InlineKeyboardMarkup:
        """
        Genera el teclado del Menú Principal con estilos nativos.
        """
        keyboard = [
            [
                BotKeyboards.btn(
                    "📖 Catálogo de Series",
                    callback_data="nav_local|all_series",
                    style="primary",
                ),
                BotKeyboards.btn(
                    "⭐ Novedades",
                    callback_data="nav_local|newest",
                    style="primary",
                ),
            ],
            [
                BotKeyboards.btn("🏷️ Géneros", callback_data="nav_local|genres"),
                BotKeyboards.btn("✍️ Autores", callback_data="nav_local|authors"),
            ],
            [
                BotKeyboards.btn("🔍 Buscar Novela", callback_data="buscar"),
            ],
        ]

        if show_webapp and webapp_url:
            keyboard.append(
                [
                    BotKeyboards.btn(
                        "🌐 Abrir ZeePub Web", url=webapp_url, style="primary"
                    ),
                    BotKeyboards.btn(
                        "❌ Salir", callback_data="cerrar", style="danger"
                    ),
                ]
            )
        else:
            keyboard.append(
                [BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger")]
            )

        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 🏷️ REJILLA DE GÉNEROS
    # ---------------------------------------------------------
    @staticmethod
    def genres_grid(genres: list[str]) -> InlineKeyboardMarkup:
        """
        Muestra la lista de géneros en formato cuadrícula (2 columnas) con barra de navegación Zero Dead-Ends.
        """
        keyboard = []
        for i in range(0, len(genres), 2):
            row = [BotKeyboards.btn(f"🏷️ {genres[i]}", callback_data=f"gen|{genres[i]}")]
            if i + 1 < len(genres):
                row.append(
                    BotKeyboards.btn(
                        f"🏷️ {genres[i + 1]}", callback_data=f"gen|{genres[i + 1]}"
                    )
                )
            keyboard.append(row)

        # Barra de navegación Zero Dead-Ends
        keyboard.append(
            [
                BotKeyboards.btn("⬅️ Volver", callback_data="subir_nivel"),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📖 LISTADO PAGINADO DE SERIES
    # ---------------------------------------------------------
    @staticmethod
    def series_list(
        items: list[dict],
        origin_type: str,
        filter_val: str | None,
        page: int,
        total_pages: int,
    ) -> InlineKeyboardMarkup:
        """
        Lista vertical de series con paginador enriquecido y anclas de retorno.
        """
        keyboard = []

        # 1. Filas de Series
        for item in items:
            title = item.get("title", "Novela")
            idx = item.get("index", 0)
            s_hash = item.get("series_hash")
            cb = f"col|{str(s_hash)[:24]}" if s_hash else f"col|{idx}"
            keyboard.append([BotKeyboards.btn(f"📁 {title}", callback_data=cb)])

        # 2. Fila de Paginación Inteligente
        nav_row = []
        safe_filter = filter_val or ""

        if page > 1:
            nav_row.append(
                BotKeyboards.btn(
                    "◀️ Ant.",
                    callback_data=f"nav_p|{origin_type}|{safe_filter}|{page - 1}",
                    style="primary",
                )
            )
        else:
            nav_row.append(BotKeyboards.btn("⛔ 1", callback_data="noop"))

        # Indicador central de página
        display_total = max(1, total_pages)
        nav_row.append(
            BotKeyboards.btn(f"📄 {page}/{display_total}", callback_data="noop")
        )

        if page < total_pages:
            nav_row.append(
                BotKeyboards.btn(
                    "Sig. ▶️",
                    callback_data=f"nav_p|{origin_type}|{safe_filter}|{page + 1}",
                    style="primary",
                )
            )
        else:
            nav_row.append(
                BotKeyboards.btn(f"⛔ {display_total}", callback_data="noop")
            )

        keyboard.append(nav_row)

        # 3. Anclas de Navegación Zero Dead-Ends
        keyboard.append(
            [
                BotKeyboards.btn("⬅️ Volver", callback_data="subir_nivel"),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📚 LISTADO PAGINADO DE LIBROS SUELTOS
    # ---------------------------------------------------------
    @staticmethod
    def books_list(
        items: list[dict],
        origin_type: str,
        filter_val: str | None,
        page: int,
        total_pages: int,
    ) -> InlineKeyboardMarkup:
        """
        Lista paginada de libros con semiótica 📕 y paginación táctil.
        """
        keyboard = []

        for b in items:
            key = b["key"]
            display = b.get("display") or f"📕 {b.get('title', 'Libro')}"
            if len(display) > 34:
                display = display[:31] + "..."
            keyboard.append([BotKeyboards.btn(display, callback_data=f"lib|{key}")])

        # Paginador
        nav_row = []
        safe_filter = filter_val or ""
        if page > 1:
            nav_row.append(
                BotKeyboards.btn(
                    "◀️ Ant.",
                    callback_data=f"nav_b|{origin_type}|{safe_filter}|{page - 1}",
                    style="primary",
                )
            )
        else:
            nav_row.append(BotKeyboards.btn("⛔ 1", callback_data="noop"))

        display_total = max(1, total_pages)
        nav_row.append(
            BotKeyboards.btn(f"📄 {page}/{display_total}", callback_data="noop")
        )

        if page < total_pages:
            nav_row.append(
                BotKeyboards.btn(
                    "Sig. ▶️",
                    callback_data=f"nav_b|{origin_type}|{safe_filter}|{page + 1}",
                    style="primary",
                )
            )
        else:
            nav_row.append(
                BotKeyboards.btn(f"⛔ {display_total}", callback_data="noop")
            )

        keyboard.append(nav_row)

        # Barra de retorno
        keyboard.append(
            [
                BotKeyboards.btn("⬅️ Volver", callback_data="subir_nivel"),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # ✍️ LISTADO PAGINADO DE AUTORES
    # ---------------------------------------------------------
    @staticmethod
    def authors_list(
        authors: list[str], page: int, total_pages: int
    ) -> InlineKeyboardMarkup:
        """Lista de autores paginada con semiótica ✍️ y control de límites."""
        keyboard = []
        for auth in authors:
            display_auth = f"✍️ {auth}"
            if len(display_auth) > 34:
                display_auth = display_auth[:31] + "..."
            keyboard.append(
                [BotKeyboards.btn(display_auth, callback_data=f"aut|{auth}")]
            )

        nav_row = []
        if page > 1:
            nav_row.append(
                BotKeyboards.btn(
                    "◀️ Ant.", callback_data=f"nav_au|{page - 1}", style="primary"
                )
            )
        else:
            nav_row.append(BotKeyboards.btn("⛔ 1", callback_data="noop"))

        display_total = max(1, total_pages)
        nav_row.append(
            BotKeyboards.btn(f"📄 {page}/{display_total}", callback_data="noop")
        )

        if page < total_pages:
            nav_row.append(
                BotKeyboards.btn(
                    "Sig. ▶️", callback_data=f"nav_au|{page + 1}", style="primary"
                )
            )
        else:
            nav_row.append(
                BotKeyboards.btn(f"⛔ {display_total}", callback_data="noop")
            )

        keyboard.append(nav_row)

        keyboard.append(
            [
                BotKeyboards.btn("⬅️ Volver", callback_data="subir_nivel"),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📖 LISTA DE VOLÚMENES POR SERIE
    # ---------------------------------------------------------
    @staticmethod
    def series_volumes(volumes: list[dict]) -> InlineKeyboardMarkup:
        """Lista interactiva de volúmenes pertenecientes a una serie."""
        keyboard = []
        for v in volumes:
            key = v["key"]
            display = v.get("display") or f"📖 Vol. {v.get('volume', 1)}"
            if len(display) > 34:
                display = display[:31] + "..."
            keyboard.append([BotKeyboards.btn(display, callback_data=f"lib|{key}")])

        keyboard.append(
            [
                BotKeyboards.btn("⬅️ Volver a Series", callback_data="volver_ultima"),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📕 FICHA TÉCNICA DEL LIBRO (DETALLES Y ACCIÓN PRIMARIA)
    # ---------------------------------------------------------
    @staticmethod
    def book_details(
        key: str,
        read_url: Optional[str] = None,
        is_admin_or_staff: bool = False,
        can_download: bool = True,
    ) -> InlineKeyboardMarkup:
        """
        Genera los botones para la ficha técnica del libro.
        - Verde 🟢: Descargar EPUB (style="success" nativo) o Deshabilitado si no hay descargas
        - Azul 🔵: Publicar en Telegram (style="primary" nativo para Admin/Staff)
        - Blanco/Gris ⚪: Volver y Menú Principal
        - Rojo 🔴: Salir (style="danger" nativo)
        """
        if can_download:
            download_btn = BotKeyboards.btn(
                "📥 Descargar EPUB",
                callback_data=f"dl_confirm|{key}",
                style="success",
            )
        else:
            download_btn = BotKeyboards.btn(
                "⛔ Descargas Agotadas Hoy",
                callback_data="noop",
                disabled=True,
            )

        keyboard = [
            [download_btn],
        ]
        if is_admin_or_staff:
            keyboard.append(
                [
                    BotKeyboards.btn(
                        "📢 Publicar en Telegram",
                        callback_data=f"pub_menu|{key}",
                        style="primary",
                    )
                ]
            )
        keyboard.append(
            [
                BotKeyboards.btn("⬅️ Volver a la Serie", callback_data="volver_ultima"),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📢 MENÚ DE PUBLICACIÓN EN TELEGRAM (ADMIN / STAFF)
    # ---------------------------------------------------------
    @staticmethod
    def publish_menu(key: str) -> InlineKeyboardMarkup:
        """
        Menú de opciones de publicación en canales para Admin y Staff.
        """
        keyboard = [
            [
                BotKeyboards.btn(
                    "⚡ Publicar Inmediatamente",
                    callback_data=f"pub_now|{key}",
                    style="success",
                ),
            ],
            [
                BotKeyboards.btn(
                    "⏰ Programar Publicación",
                    callback_data=f"pub_sched_menu|{key}",
                    style="primary",
                ),
            ],
            [
                BotKeyboards.btn(
                    "⬅️ Volver al Libro", callback_data=f"info_libro|{key}"
                ),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # ⏰ PRESETS DE PROGRAMACIÓN HORARIA (ADMIN / STAFF)
    # ---------------------------------------------------------
    @staticmethod
    def publish_schedule_presets(key: str) -> InlineKeyboardMarkup:
        """
        Presets rápidos de programación para publicación en canal.
        """
        keyboard = [
            [
                BotKeyboards.btn(
                    "🕒 En 1 Hora", callback_data=f"pub_in|1|{key}", style="primary"
                ),
                BotKeyboards.btn(
                    "🕕 En 3 Horas", callback_data=f"pub_in|3|{key}", style="primary"
                ),
            ],
            [
                BotKeyboards.btn(
                    "🌅 Mañana 10:00 AM",
                    callback_data=f"pub_preset|tomorrow_10|{key}",
                    style="primary",
                ),
                BotKeyboards.btn(
                    "🌇 Mañana 18:00 PM",
                    callback_data=f"pub_preset|tomorrow_18|{key}",
                    style="primary",
                ),
            ],
            [
                BotKeyboards.btn(
                    "⬅️ Volver a Opciones", callback_data=f"pub_menu|{key}"
                ),
                BotKeyboards.btn("❌ Cancelar", callback_data="cerrar", style="danger"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # ✅ PANTALLA POST-DESCARGA
    # ---------------------------------------------------------
    @staticmethod
    def post_download(series_hash_short: str | None = None) -> InlineKeyboardMarkup:
        """
        Opciones tras la descarga exitosa de un libro.
        """
        keyboard = []
        if series_hash_short:
            keyboard.append(
                [
                    BotKeyboards.btn(
                        "⬅️ Volver a la Serie",
                        callback_data=f"show_series|{series_hash_short}",
                    )
                ]
            )

        keyboard.append(
            [
                BotKeyboards.btn(
                    "📖 Catálogo de Series",
                    callback_data="nav_local|all_series",
                    style="primary",
                ),
                BotKeyboards.btn("🏠 Menú Principal", callback_data="volver_menu"),
            ]
        )
        keyboard.append(
            [BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger")]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 🔍 RESULTADOS DE BÚSQUEDA
    # ---------------------------------------------------------
    @staticmethod
    def search_results(
        series_items: list[dict], books_items: list[dict]
    ) -> InlineKeyboardMarkup:
        """Teclado para resultados de búsqueda combinados (Series + Libros sueltos)."""
        keyboard = []

        for s in series_items:
            title = s.get("title", "Serie")
            s_hash = s.get("series_hash")
            cb = f"col|{str(s_hash)[:24]}" if s_hash else f"col|{s['index']}"
            keyboard.append([BotKeyboards.btn(f"📁 {title}", callback_data=cb)])

        for b in books_items:
            display = b.get("display") or f"📕 {b.get('title', 'Libro')}"
            if len(display) > 34:
                display = display[:31] + "..."
            keyboard.append(
                [BotKeyboards.btn(display, callback_data=f"lib|{b['key']}")]
            )

        keyboard.append(
            [
                BotKeyboards.btn(
                    "🔍 Nueva Búsqueda", callback_data="buscar", style="primary"
                ),
                BotKeyboards.btn("🏠 Inicio", callback_data="volver_menu"),
                BotKeyboards.btn("❌ Salir", callback_data="cerrar", style="danger"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)
