import logging
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from services.library_service import LibraryService
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


async def mostrar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal basado en la BD local."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["historial"] = []
    st["current_view"] = "main"
    st["titulo"] = "📚 Biblioteca Local"

    keyboard = [
        [InlineKeyboardButton("📚 Catálogo de Libros", callback_data="nav_local|recent_books")],
        [InlineKeyboardButton("⭐ Novedades (Series)", callback_data="nav_local|newest")],
        [InlineKeyboardButton("🏷️ Géneros", callback_data="nav_local|genres")],
        [InlineKeyboardButton("✍️ Autores", callback_data="nav_local|authors")],
        [InlineKeyboardButton("📖 Todas las Series", callback_data="nav_local|all_series")],
        [InlineKeyboardButton("🔍 Buscar EPUB", callback_data="buscar")],
        [InlineKeyboardButton("❌ Salir", callback_data="cerrar")],
    ]

    text = "<b>📚 Bienvenido a la Biblioteca Local</b>\n\n🎯 <i>Selecciona una categoría para explorar nuestra colección:</i>"

    if hasattr(update, "callback_query"):
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def mostrar_generos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de géneros."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    genres = await LibraryService.get_genres()

    keyboard = []
    # Agrupar de 2 en 2
    for i in range(0, len(genres), 2):
        row = [InlineKeyboardButton(genres[i], callback_data=f"gen|{genres[i]}")]
        if i + 1 < len(genres):
            row.append(InlineKeyboardButton(genres[i + 1], callback_data=f"gen|{genres[i + 1]}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "genres"
    st["titulo"] = "🏷️ Géneros"

    text = "<b>🏷️ Selecciona un Género:</b>"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_series(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    origin_type: str,
    filter_val: str = None,
    page: int = 1,
):
    """Muestra series filtradas por tag, autor o todas."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    page_size = 10

    st["origin_type"] = origin_type
    st["filter_val"] = filter_val
    st["current_page"] = page

    if origin_type == "genre":
        data = await LibraryService.get_series_by_tag(filter_val, page=page, page_size=page_size)
        title = f"🏷️ Género: {filter_val}"
        st["prev_view_local"] = "genres"
    elif origin_type == "author":
        data = await LibraryService.get_series_by_author(filter_val, page=page, page_size=page_size)
        title = f"✍️ Autor: {filter_val}"
        st["prev_view_local"] = "authors"
    else:  # newest or all_series
        sort = "newest" if origin_type == "newest" else "a-z"
        res = await LibraryService.search_series("", page=page, items_per_page=page_size, sort_by=sort)
        data = {"items": res["results"], "total": res["totalItems"]}
        title = "⭐ Novedades" if origin_type == "newest" else "📖 Todas las Series"
        st["prev_view_local"] = "main"

    st["colecciones"] = {}
    keyboard = []

    for i, s in enumerate(data["items"]):
        href = f"local_series|{s['series_hash']}"
        st["colecciones"][i] = {"titulo": s["title"], "href": href}
        keyboard.append([InlineKeyboardButton(s["title"], callback_data=f"col|{i}")])

    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton("⬅️ Ant.", callback_data=f"nav_p|{origin_type}|{filter_val or ''}|{page - 1}")
        )
    if page * page_size < data["total"]:
        nav_row.append(
            InlineKeyboardButton("Sig. ➡️", callback_data=f"nav_p|{origin_type}|{filter_val or ''}|{page + 1}")
        )

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "series_list"
    st["titulo"] = title

    text = f"<b>{title}</b>\nResultados: {data['total']} series."
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_libros(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    origin_type: str = "recent",
    filter_val: str = None,
    page: int = 1,
):
    """Muestra libros filtrados o recientes (paginados 10 max)."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    page_size = 10

    st["origin_type_b"] = origin_type
    st["filter_val_b"] = filter_val
    st["current_page_b"] = page
    st["prev_view_local"] = "main"

    if origin_type == "recent":
        # Usamos el nuevo fetcher de LibraryService
        data = await LibraryService.get_recent_books(page=page, items_per_page=page_size)
    else:
        # Fallback futuro
        data = {"items": [], "totalItems": 0, "totalPages": 0}

    st["libros"] = {}
    keyboard = []

    for b in data.get("items", []):
        key = uuid.uuid4().hex[:8]
        st["libros"][key] = {
            "titulo": b["title"],
            "autor": b["author"],
            "descarga": b["filepath"],
            "portada": b.get("coverUrl", b.get("cover_medium") or b.get("cover_low")),
            "hash": b["book_hash"],
        }

        display = f"📕 {b['title']}"
        if len(display) > 35:
            display = display[:32] + "..."

        keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

    nav_row = []
    if page > 1:
        nav_row.append(
            InlineKeyboardButton("⬅️ Ant.", callback_data=f"nav_b|{origin_type}|{filter_val or ''}|{page - 1}")
        )
    if page < data.get("totalPages", 1):
        nav_row.append(
            InlineKeyboardButton("Sig. ➡️", callback_data=f"nav_b|{origin_type}|{filter_val or ''}|{page + 1}")
        )

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "books_list"
    title = "📚 Catálogo de Libros" if origin_type == "recent" else "📖 Libros"
    st["titulo"] = title

    text = f"<b>{title}</b>\n✨ Explorando {data.get('totalItems', 0)} libros disponibles (Pág. {page}/{data.get('totalPages', 1)})."

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_volumenes_local(update: Update, context: ContextTypes.DEFAULT_TYPE, series_hash: str):
    """Muestra volúmenes de una serie local."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    volumes = await LibraryService.get_series_volumes(series_hash)
    meta = await LibraryService.get_series_metadata(series_hash)

    series_name = meta.series_name if meta else "Serie"
    st["libros"] = {}
    keyboard = []

    for v in volumes:
        key = uuid.uuid4().hex[:8]
        st["libros"][key] = {
            "titulo": v["title"],
            "autor": v["author"],
            "descarga": v["filepath"],
            "portada": v.get("cover_medium") or v.get("cover_low"),
            "hash": v["book_hash"],
        }

        display = f"Vol. {v['volume']}" if v.get("volume") else v["title"]
        if len(display) > 35:
            display = display[:32] + "..."

        keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "volumes_local"
    st["current_series_hash"] = series_hash

    text = f"<b>📖 {series_name}</b>\n\nSelecciona un volumen para descargar:"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_autores_local(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de autores locales."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    authors = await LibraryService.get_authors()

    keyboard = []
    # Autores suelen ser muchos, mostrar de 1 en 1 o 2 en 2
    for i in range(0, len(authors), 1):
        keyboard.append([InlineKeyboardButton(authors[i], callback_data=f"aut|{authors[i]}")])
        if i > 50:  # Evitar teclados gigantescos
            keyboard.append([InlineKeyboardButton("... y más", callback_data="none")])
            break

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "authors"
    st["titulo"] = "✍️ Autores"

    text = "<b>✍️ Selecciona un Autor:</b>"
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_resultados_locales(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str, results: list):
    """Muestra los resultados de una búsqueda local."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["libros"] = {}
    keyboard = []

    for b in results:
        key = uuid.uuid4().hex[:8]
        st["libros"][key] = {
            "titulo": b["title"],
            "autor": b["author"],
            "descarga": b["filepath"],
            "portada": b.get("cover_medium") or b.get("cover_low"),
            "hash": b["book_hash"],
        }

        display = b["title"]
        if len(display) > 35:
            display = display[:32] + "..."

        keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "search_results"
    st["titulo"] = f"🔍 Resultados: {query}"

    text = f"<b>🔍 Resultados para:</b> {query}\nEncontrados: {len(results)} libros."

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )
    else:
        # Si viene de handle_search_text (mensaje nuevo)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )
