import logging
import os
import uuid

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from services.library_service import LibraryService
from utils.helpers import get_thread_id, get_translator_acronym

logger = logging.getLogger(__name__)


async def mostrar_menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal basado en la BD local."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["historial"] = []
    st["current_view"] = "main"
    st["titulo"] = "📚 Biblioteca Local"

    keyboard = [
        [InlineKeyboardButton("📖 Catálogo de Series", callback_data="nav_local|all_series")],
        [InlineKeyboardButton("⭐ Novedades (Series)", callback_data="nav_local|newest")],
        [InlineKeyboardButton("🏷️ Géneros", callback_data="nav_local|genres")],
        [InlineKeyboardButton("✍️ Autores", callback_data="nav_local|authors")],
        [InlineKeyboardButton("🔍 Buscar EPUB", callback_data="buscar")],
        [InlineKeyboardButton("❌ Salir", callback_data="cerrar")],
    ]

    text = "<b>📚 Bienvenido a la Biblioteca Local</b>\n\n🎯 <i>Selecciona una categoría para explorar nuestra colección:</i>"

    if update.callback_query:
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

    nav_row = [InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")]
    if page > 1:
        nav_row.append(
            InlineKeyboardButton("⬅️ Ant.", callback_data=f"nav_p|{origin_type}|{filter_val or ''}|{page - 1}")
        )
    if page * page_size < data["total"]:
        nav_row.append(
            InlineKeyboardButton("Sig. ➡️", callback_data=f"nav_p|{origin_type}|{filter_val or ''}|{page + 1}")
        )

    keyboard.append(nav_row)

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

    nav_row = [InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")]
    if page > 1:
        nav_row.append(
            InlineKeyboardButton("⬅️ Ant.", callback_data=f"nav_b|{origin_type}|{filter_val or ''}|{page - 1}")
        )
    if page < data.get("totalPages", 1):
        nav_row.append(
            InlineKeyboardButton("Sig. ➡️", callback_data=f"nav_b|{origin_type}|{filter_val or ''}|{page + 1}")
        )

    keyboard.append(nav_row)

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
        # Nuevo formato: Vol. X [TR] [Color]
        vol = v.get("volume")
        if vol is not None:
            vol_display = int(vol) if float(vol).is_integer() else vol
            vol_str = f"Vol. {vol_display}"
        else:
            vol_str = v.get("title", "")

        translator = v.get("translator")
        # Preferimos siglas de BD, si no hay, usamos heurística
        tr_acronym = v.get("translator_siglas") or get_translator_acronym(translator)

        is_color = v.get("color_mode") == "color"
        color_tag = " [🎨]" if is_color else ""

        display = f"{vol_str} [{tr_acronym}]{color_tag}"

        st["libros"][key] = {
            "titulo": v.get("title", ""),
            "autor": v.get("author", ""),
            "descarga": v.get("filepath", "N/A"),
            "portada": v.get("coverUrl", ""),
            "hash": v.get("book_hash", ""),
            "display": display,
            "series": series_name,
            "volume": vol,
            "translator": translator,
            "translator_siglas": tr_acronym,
            "color": is_color,
        }

        if len(display) > 35:
            display = display[:32] + "..."

        keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "volumes_local"
    st["current_series_hash"] = series_hash

    text = f"<b>📖 {series_name}</b>\n\nSelecciona un volumen para obtener más detalles:"
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


async def mostrar_detalles_libro(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str):
    """Muestra la ficha técnica del libro y confirmación de descarga."""
    from utils.download_limiter import downloads_left

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    libro = st.get("libros", {}).get(key)

    if not libro:
        if update.callback_query:
            await update.callback_query.answer("⚠️ Libro no encontrado.", show_alert=True)
        return

    # Info de descargas
    left = await downloads_left(uid)
    left_str = f"descargas restantes hoy: <b>{left}</b>" if isinstance(left, int) else "descargas <b>ilimitadas</b>"

    # Construir ficha
    text = f"<b>📖 {libro['titulo']}</b>\n"
    if libro.get("series"):
        v_num = libro.get("volume")
        v_str = f" Vol. {int(v_num) if float(v_num or 0).is_integer() else v_num}" if v_num else ""
        text += f"📚 Serie: {libro['series']}{v_str}\n"

    if libro.get("autor"):
        text += f"✍️ Autor: {libro['autor']}\n"

    tr = libro.get("translator")
    sigla = libro.get("translator_siglas")
    if tr:
        text += f"🌐 Traducción: {tr} ({sigla})\n" if sigla else f"🌐 Traducción: {tr}\n"

    if libro.get("color"):
        text += "🎨 Edición: <b>Color</b>\n"

    text += f"\n📥 Tienes {left_str}."

    keyboard = [
        [InlineKeyboardButton("📥 Descargar volumen", callback_data=f"dl_confirm|{key}")],
        [InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")],
    ]

    portada = libro.get("portada")

    if update.callback_query:
        # Intentar borrar el anterior y mandar foto si hay portada
        try:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id, message_id=update.callback_query.message.message_id
            )
        except Exception:
            pass

    if portada and (portada.startswith("http") or os.path.exists(portada)):
        from services.cover_service import send_photo_bytes

        await send_photo_bytes(
            context.bot,
            update.effective_chat.id,
            text,
            portada,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_autores_local(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    """Muestra lista de autores locales paginada."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    page_size = 10

    data = await LibraryService.get_authors(page=page, page_size=page_size)
    authors = data["items"]
    total = data["total"]

    keyboard = []
    # Mostramos de 1 en 1 para mayor claridad
    for auth in authors:
        keyboard.append([InlineKeyboardButton(auth, callback_data=f"aut|{auth}")])

    nav_row = [InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")]
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Ant.", callback_data=f"nav_au|{page - 1}"))
    if page * page_size < total:
        nav_row.append(InlineKeyboardButton("Sig. ➡️", callback_data=f"nav_au|{page + 1}"))

    keyboard.append(nav_row)

    st["current_view"] = "authors"
    st["titulo"] = "✍️ Autores"

    text = f"<b>✍️ Selecciona un Autor:</b>\nMostrando {len(authors)} autores (Pág. {page})."
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


async def mostrar_resultados_locales(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    series: list,
    books_standalone: list = None,
):
    """Muestra los resultados de una búsqueda local agrupada por series."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["libros"] = {}
    st["colecciones"] = {}
    keyboard = []

    # 1. Agregar Series (Resultados agrupados)
    if series:
        for i, s in enumerate(series):
            # Límite para no saturar el mensaje de Telegram
            if i >= 15:
                break
            href = f"local_series|{s['series_hash']}"
            st["colecciones"][i] = {"titulo": s["title"], "href": href}
            keyboard.append([InlineKeyboardButton(f"📁 {s['title']}", callback_data=f"col|{i}")])

    # 2. Agregar Libros "Sueltos" (que no pertenecen a las series encontradas o no tienen serie)
    if books_standalone:
        for b in books_standalone:
            # Si ya tenemos suficientes botones, paramos
            if len(keyboard) >= 20:
                break
            key = uuid.uuid4().hex[:8]
            st["libros"][key] = {
                "titulo": b["title"],
                "autor": b["author"],
                "descarga": b["filepath"],
                "portada": b.get("cover_medium") or b.get("cover_low"),
                "hash": b["book_hash"],
            }

            display = f"📕 {b['title']}"
            if len(display) > 35:
                display = display[:32] + "..."

            keyboard.append([InlineKeyboardButton(display, callback_data=f"lib|{key}")])

    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="subir_nivel")])

    st["current_view"] = "search_results"
    st["titulo"] = f"🔍 Resultado: {query}"

    total_s = len(series) if series else 0
    total_b = len(books_standalone) if books_standalone else 0

    if total_s > 0 or total_b > 0:
        text = f"<b>🔍 Resultados para:</b> {query}\n"
        if total_s > 0:
            text += f"📂 Encontradas <b>{total_s}</b> series.\n"
        if total_b > 0:
            text += f"📕 Encontrados <b>{total_b}</b> libros individuales.\n"
    else:
        text = f"❌ No se han encontrado resultados para: <b>{query}</b>"

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
