from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from models.library import Book, Series


class UIServiceV4:
    """
    Servicio de UI v4.0 enfocado en estética Premium/Glassmorphism y consistencia visual.
    Centraliza la generación de textos y teclados para Telegram.
    """

    @staticmethod
    def get_glass_header(title: str) -> str:
        """Genera un encabezado con estilo premium."""
        return f"✨ <b>{title.upper()}</b>\n" + "—" * 15 + "\n\n"

    @classmethod
    async def render_main_menu(cls) -> tuple[str, InlineKeyboardMarkup]:
        """Genera el menú principal v4.0."""
        text = (
            f"{cls.get_glass_header('ZeePub Enterprise')}"
            "Bienvenido a la biblioteca digital definitiva.\n\n"
            "🎯 <b>¿Qué deseas explorar hoy?</b>"
        )
        keyboard = [
            [InlineKeyboardButton("📖 Catálogo Completo", callback_data="catalog|0")],
            [InlineKeyboardButton("🔍 Buscador Avanzado", callback_data="search_init")],
            [InlineKeyboardButton("👤 Mi Perfil / Status", callback_data="user_status")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")],
        ]
        return text, InlineKeyboardMarkup(keyboard)

    @classmethod
    async def render_series_list(cls, series_list: list[Series], page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
        """Genera la lista de series para el catálogo."""
        text = f"{cls.get_glass_header('Catálogo de Series')}Mostrando <b>{len(series_list)}</b> obras disponibles:"
        keyboard = []
        for s in series_list:
            # Limitar longitud del nombre para botones
            display_name = s.name if len(s.name) < 30 else s.name[:27] + "..."
            keyboard.append([InlineKeyboardButton(f"📖 {display_name}", callback_data=f"series_view|{s.id}")])

        # Fila de navegación
        nav_row = [InlineKeyboardButton("🏠 Menú", callback_data="main_menu")]
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"catalog|{page - 1}"))
        if len(series_list) >= 10:
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"catalog|{page + 1}"))

        keyboard.append(nav_row)
        return text, InlineKeyboardMarkup(keyboard)

    @classmethod
    async def render_series_details(cls, series: Series, books: list[Book]) -> tuple[str, InlineKeyboardMarkup]:
        """Genera la ficha de una serie y sus volúmenes."""
        text = (
            f"{cls.get_glass_header(series.name)}"
            f"📝 <b>Sinopsis:</b>\n<i>{series.description or 'Sin descripción disponible.'}</i>\n\n"
            "📦 <b>Volúmenes disponibles:</b>"
        )
        keyboard = []
        for b in books:
            keyboard.append([InlineKeyboardButton(f"📕 {b.title}", callback_data=f"book_view|{b.id}")])

        keyboard.append([InlineKeyboardButton("🔙 Volver al Catálogo", callback_data="catalog|0")])
        return text, InlineKeyboardMarkup(keyboard)

    @classmethod
    async def render_book_details(cls, book: Book) -> tuple[str, InlineKeyboardMarkup]:
        """Genera la ficha técnica de un libro específico."""
        text = (
            f"📕 <b>{book.title}</b>\n"
            f"👤 <b>Autor:</b> {book.author or 'Desconocido'}\n"
            f"🏷️ <b>Hash:</b> <code>{book.id[:8]}</code>\n\n"
            "¿Deseas descargar este ejemplar?"
        )
        keyboard = [
            [InlineKeyboardButton("⚡️ Descargar Ahora", callback_data=f"book_download|{book.id}")],
            [InlineKeyboardButton("🔙 Volver a la Serie", callback_data=f"series_view|{book.series_id}")],
            [InlineKeyboardButton("❌ Salir", callback_data="close_menu")],
        ]
        return text, InlineKeyboardMarkup(keyboard)
