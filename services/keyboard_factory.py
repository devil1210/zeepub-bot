# services/keyboard_factory.py
"""
Factory de Teclados Interactivos para Telegram (ZeePub-bot v3.6+).
Garantiza semiótica de color estricta por emojis, diseño responsivo y límites de 64 bytes en callback_data.
Sigue el principio Zero Dead-Ends (ningún menú deja al usuario sin salida o navegación de retorno).
"""

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class BotKeyboards:
    """Constructor centralizado de teclados interactivos con semiótica cromática."""

    # ---------------------------------------------------------
    # 🏠 MENÚ PRINCIPAL
    # ---------------------------------------------------------
    @staticmethod
    def main_menu(webapp_url: Optional[str] = None) -> InlineKeyboardMarkup:
        """
        Genera el teclado del Menú Principal.
        Semiótica:
        - 🔵 Azul: Exploración (Catálogo, Géneros, Autores, Buscar)
        - 🟡 Amarillo: Novedades / Destacados
        - 🔴 Rojo: Salir / Cerrar
        """
        keyboard = [
            [
                InlineKeyboardButton(
                    "📖 Catálogo de Series", callback_data="nav_local|all_series"
                ),
                InlineKeyboardButton(
                    "⭐ Novedades", callback_data="nav_local|newest"
                ),
            ],
            [
                InlineKeyboardButton("🏷️ Géneros", callback_data="nav_local|genres"),
                InlineKeyboardButton("✍️ Autores", callback_data="nav_local|authors"),
            ],
            [
                InlineKeyboardButton("🔍 Buscar Novela", callback_data="buscar"),
            ],
        ]

        if webapp_url:
            keyboard.append(
                [
                    InlineKeyboardButton("🌐 Abrir ZeePub Web", url=webapp_url),
                    InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
                ]
            )
        else:
            keyboard.append([InlineKeyboardButton("❌ Salir", callback_data="cerrar")])

        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 🏷️ REJILLA DE GÉNEROS
    # ---------------------------------------------------------
    @staticmethod
    def genres_grid(genres: List[str]) -> InlineKeyboardMarkup:
        """
        Muestra la lista de géneros en formato cuadrícula (2 columnas) con barra de navegación Zero Dead-Ends.
        """
        keyboard = []
        for i in range(0, len(genres), 2):
            row = [InlineKeyboardButton(f"🏷️ {genres[i]}", callback_data=f"gen|{genres[i]}")]
            if i + 1 < len(genres):
                row.append(
                    InlineKeyboardButton(
                        f"🏷️ {genres[i + 1]}", callback_data=f"gen|{genres[i + 1]}"
                    )
                )
            keyboard.append(row)

        # Barra de navegación Zero Dead-Ends
        keyboard.append(
            [
                InlineKeyboardButton("⬅️ Volver", callback_data="subir_nivel"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📖 LISTADO PAGINADO DE SERIES
    # ---------------------------------------------------------
    @staticmethod
    def series_list(
        items: List[dict],
        origin_type: str,
        filter_val: Optional[str],
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
            if len(title) > 34:
                title = title[:31] + "..."
            keyboard.append([InlineKeyboardButton(f"📁 {title}", callback_data=f"col|{idx}")])

        # 2. Fila de Paginación Inteligente
        nav_row = []
        safe_filter = filter_val or ""
        
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    "◀️ Ant.",
                    callback_data=f"nav_p|{origin_type}|{safe_filter}|{page - 1}",
                )
            )
        else:
            nav_row.append(InlineKeyboardButton("⛔ 1", callback_data="noop"))

        # Indicador central de página
        display_total = max(1, total_pages)
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{display_total}", callback_data="noop"))

        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    "Sig. ▶️",
                    callback_data=f"nav_p|{origin_type}|{safe_filter}|{page + 1}",
                )
            )
        else:
            nav_row.append(InlineKeyboardButton(f"⛔ {display_total}", callback_data="noop"))

        keyboard.append(nav_row)

        # 3. Anclas de Navegación Zero Dead-Ends
        keyboard.append(
            [
                InlineKeyboardButton("⬅️ Volver", callback_data="subir_nivel"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📚 LISTADO PAGINADO DE LIBROS SUELTOS
    # ---------------------------------------------------------
    @staticmethod
    def books_list(
        items: List[dict],
        origin_type: str,
        filter_val: Optional[str],
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
            keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

        # Paginador
        nav_row = []
        safe_filter = filter_val or ""
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(
                    "◀️ Ant.",
                    callback_data=f"nav_b|{origin_type}|{safe_filter}|{page - 1}",
                )
            )
        else:
            nav_row.append(InlineKeyboardButton("⛔ 1", callback_data="noop"))

        display_total = max(1, total_pages)
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{display_total}", callback_data="noop"))

        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(
                    "Sig. ▶️",
                    callback_data=f"nav_b|{origin_type}|{safe_filter}|{page + 1}",
                )
            )
        else:
            nav_row.append(InlineKeyboardButton(f"⛔ {display_total}", callback_data="noop"))

        keyboard.append(nav_row)

        # Barra de retorno
        keyboard.append(
            [
                InlineKeyboardButton("⬅️ Volver", callback_data="subir_nivel"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # ✍️ LISTADO PAGINADO DE AUTORES
    # ---------------------------------------------------------
    @staticmethod
    def authors_list(
        authors: List[str], page: int, total_pages: int
    ) -> InlineKeyboardMarkup:
        """Lista de autores paginada con semiótica ✍️ y control de límites."""
        keyboard = []
        for auth in authors:
            display_auth = f"✍️ {auth}"
            if len(display_auth) > 34:
                display_auth = display_auth[:31] + "..."
            keyboard.append([InlineKeyboardButton(display_auth, callback_data=f"aut|{auth}")])

        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton("◀️ Ant.", callback_data=f"nav_au|{page - 1}")
            )
        else:
            nav_row.append(InlineKeyboardButton("⛔ 1", callback_data="noop"))

        display_total = max(1, total_pages)
        nav_row.append(InlineKeyboardButton(f"📄 {page}/{display_total}", callback_data="noop"))

        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton("Sig. ▶️", callback_data=f"nav_au|{page + 1}")
            )
        else:
            nav_row.append(InlineKeyboardButton(f"⛔ {display_total}", callback_data="noop"))

        keyboard.append(nav_row)

        keyboard.append(
            [
                InlineKeyboardButton("⬅️ Volver", callback_data="subir_nivel"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 📖 LISTA DE VOLÚMENES POR SERIE
    # ---------------------------------------------------------
    @staticmethod
    def series_volumes(volumes: List[dict]) -> InlineKeyboardMarkup:
        """Lista interactiva de volúmenes pertenecientes a una serie."""
        keyboard = []
        for v in volumes:
            key = v["key"]
            display = v.get("display") or f"📖 Vol. {v.get('volume', 1)}"
            if len(display) > 34:
                display = display[:31] + "..."
            keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

        keyboard.append(
            [
                InlineKeyboardButton("⬅️ Volver a Series", callback_data="volver_ultima"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
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
    ) -> InlineKeyboardMarkup:
        """
        Genera los botones para la ficha técnica del libro.
        - Verde 🟢: Descargar EPUB (Acción principal)
        - Azul 🔵: Leer Online (si está disponible)
        - Blanco/Gris ⚪: Volver y Menú Principal
        - Rojo 🔴: Salir
        """
        top_row = [
            InlineKeyboardButton("📥 Descargar EPUB", callback_data=f"dl_confirm|{key}")
        ]
        if read_url:
            top_row.append(InlineKeyboardButton("📖 Leer Online", url=read_url))

        keyboard = [
            top_row,
            [
                InlineKeyboardButton("⬅️ Volver a la Serie", callback_data="volver_ultima"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # ✅ PANTALLA POST-DESCARGA
    # ---------------------------------------------------------
    @staticmethod
    def post_download(series_hash_short: Optional[str] = None) -> InlineKeyboardMarkup:
        """
        Opciones tras la descarga exitosa de un libro.
        """
        keyboard = []
        if series_hash_short:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "⬅️ Volver a la Serie",
                        callback_data=f"show_series|{series_hash_short}",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "📖 Catálogo de Series", callback_data="nav_local|all_series"
                ),
                InlineKeyboardButton("🏠 Menú Principal", callback_data="volver_menu"),
            ]
        )
        keyboard.append([InlineKeyboardButton("❌ Salir", callback_data="cerrar")])
        return InlineKeyboardMarkup(keyboard)

    # ---------------------------------------------------------
    # 🔍 RESULTADOS DE BÚSQUEDA
    # ---------------------------------------------------------
    @staticmethod
    def search_results(
        series_items: List[dict], books_items: List[dict]
    ) -> InlineKeyboardMarkup:
        """Teclado para resultados de búsqueda combinados (Series + Libros sueltos)."""
        keyboard = []

        for s in series_items:
            title = s.get("title", "Serie")
            if len(title) > 34:
                title = title[:31] + "..."
            keyboard.append(
                [InlineKeyboardButton(f"📁 {title}", callback_data=f"col|{s['index']}")]
            )

        for b in books_items:
            display = b.get("display") or f"📕 {b.get('title', 'Libro')}"
            if len(display) > 34:
                display = display[:31] + "..."
            keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{b['key']}")])

        keyboard.append(
            [
                InlineKeyboardButton("🔍 Nueva Búsqueda", callback_data="buscar"),
                InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
            ]
        )
        return InlineKeyboardMarkup(keyboard)
