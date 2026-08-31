# services/library_ui/catalog_views.py
"""
Vistas interactivas de Catálogo, Menú Principal, Géneros, Autores y Buscador para Telegram.
"""

import logging
import uuid
from telegram import Update
from telegram.ext import ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.keyboard_factory import BotKeyboards
from services.library_service import LibraryService
from services.rich_message_service import RichMessageService
from utils.download_limiter import downloads_left
from utils.helpers import get_thread_id

from .builders import (
    build_authors_rich_blocks,
    build_genres_rich_blocks,
    build_main_menu_rich_blocks,
    build_search_prompt_rich_blocks,
    build_search_results_rich_blocks,
    build_series_catalog_rich_blocks,
)

logger = logging.getLogger(__name__)


async def check_is_admin_or_staff(uid: int, tg_user=None) -> bool:
    """Verifica si el usuario tiene privilegios de Admin o Staff/Publicador."""
    try:
        from services.user_service import get_effective_user

        info = await get_effective_user(uid, tg_user=tg_user)
        if (
            info.get("is_real_admin")
            or info.get("role") in ["admin", "staff", "Publicador"]
            or info.get("level") in ["admin", "staff"]
        ):
            return True
        from config.config_settings import config

        if uid in getattr(config, "ADMIN_USERS", []):
            return True
    except Exception as e:
        logger.debug(f"Error verificando rol admin/staff para {uid}: {e}")
    return False


async def mostrar_menu_principal(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra el menú principal en formato Rich Message unificado con estadísticas en vivo."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)

    st["historial"] = []
    st["current_view"] = "main"
    st["titulo"] = "📚 Biblioteca Digital"

    is_staff = await check_is_admin_or_staff(uid, update.effective_user)
    webapp_url = getattr(config, "WEBAPP_URL", None)

    # 1. Estadísticas globales y cuota
    stats = await LibraryService.get_library_stats()
    user_name = update.effective_user.first_name or "Lector"
    left = await downloads_left(uid)
    if left == "ilimitadas":
        downloads_str = "Ilimitadas"
    elif isinstance(left, int):
        downloads_str = f"{left} disponibles"
    else:
        downloads_str = str(left)

    user_rank = "👑 Administrador" if is_staff else "📖 Lector"

    # 2. Bloques Nativos (Rich Blocks)
    blocks = build_main_menu_rich_blocks(
        user_name=user_name,
        stats=stats,
        downloads_str=downloads_str,
        user_rank=user_rank,
        webapp_url=webapp_url,
        show_webapp=is_staff,
    )

    # 3. Intentar editar in-place si proviene de un callback
    if update.callback_query and not force_new:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            if res_edit and res_edit.get("ok"):
                return
        except Exception as e:
            logger.debug(f"[mostrar_menu_principal] Falló edit_rich_message: {e}")

    # 4. Enviar nuevo Rich Message
    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )

    # 5. Fallback tradicional si falla Rich Message
    if not res or not res.get("ok"):
        reply_markup = BotKeyboards.main_menu(
            webapp_url=webapp_url, show_webapp=is_staff
        )
        text = (
            f"<b>🌟 ZeePubs • Biblioteca Digital</b>\n\n"
            f"¡Hola, <b>{user_name}</b>! Bienvenido a tu portal de lectura de Novelas Ligeras.\n\n"
            f"📚 <b>Series:</b> {stats.get('series_count', 0)} | 📖 <b>Libros:</b> {stats.get('books_count', 0)}\n"
            f"📥 <b>Cuota hoy:</b> {downloads_str} | 👤 <b>Rango:</b> {user_rank}\n\n"
            f"🎯 <b>¿Qué te apetece leer hoy?</b>"
        )
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )


async def mostrar_generos(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra lista de géneros en formato Rich Message unificado."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)

    genres = await LibraryService.get_genres()

    st["current_view"] = "genres"
    st["prev_view_local"] = "main"
    st["titulo"] = "🏷️ Géneros"

    blocks = build_genres_rich_blocks(genres)

    if update.callback_query and not force_new:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            if res_edit and res_edit.get("ok"):
                return
        except Exception as e:
            logger.debug(f"[mostrar_generos] Falló edit_rich_message: {e}")

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )

    if not res or not res.get("ok"):
        reply_markup = BotKeyboards.genres_grid(genres)
        text = "<b>🏷️ Selecciona un Género:</b>"
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )


async def mostrar_series(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    origin_type: str,
    filter_val: str = None,
    page: int = 1,
    force_new: bool = False,
):
    """Muestra series filtradas por tag, autor o todas en formato Rich Message unificado."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)
    page_size = 6

    st["origin_type"] = origin_type
    st["filter_val"] = filter_val
    st["current_page"] = page

    if origin_type == "genre":
        data = await LibraryService.get_series_by_tag(
            filter_val, page=page, page_size=page_size
        )
        title = f"🏷️ Género: {filter_val}"
        st["prev_view_local"] = "genres"
    elif origin_type == "author":
        data = await LibraryService.get_series_by_author(
            filter_val, page=page, page_size=page_size
        )
        title = f"✍️ Autor: {filter_val}"
        st["prev_view_local"] = "authors"
    else:  # newest or all_series
        sort = "newest" if origin_type == "newest" else "a-z"
        res = await LibraryService.search_series(
            "", page=page, items_per_page=page_size, sort_by=sort
        )
        data = {"items": res["results"], "total": res["totalItems"]}
        title = "⭐ Novedades" if origin_type == "newest" else "📖 Todas las Series"
        st["prev_view_local"] = "main"

    st["colecciones"] = {}
    items = []

    for i, s in enumerate(data["items"]):
        href = f"local_series|{s['series_hash']}"
        series_title = s.get("name") or s.get("series_name") or s.get("title", "Novela")
        book_count = s.get("book_count") or s.get("count") or 1
        st["colecciones"][i] = {"titulo": series_title, "href": href}
        items.append({"title": series_title, "index": i, "book_count": book_count})

    total_pages = (data["total"] + page_size - 1) // page_size if data["total"] > 0 else 1
    st["current_view"] = "series_list"
    st["titulo"] = title

    blocks = build_series_catalog_rich_blocks(
        title=title,
        items=items,
        total_series=data["total"],
        page=page,
        total_pages=total_pages,
        origin_type=origin_type,
        filter_val=filter_val,
    )

    if update.callback_query and not force_new:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            if res_edit and res_edit.get("ok"):
                return
        except Exception as e:
            logger.debug(f"[mostrar_series] Falló edit_rich_message: {e}")

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )

    if not res or not res.get("ok"):
        reply_markup = BotKeyboards.series_list(
            items=items,
            origin_type=origin_type,
            filter_val=filter_val,
            page=page,
            total_pages=total_pages,
        )
        text = f"<b>{title}</b>\nResultados: {data['total']} series."
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
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
        data = await LibraryService.get_recent_books(
            page=page, items_per_page=page_size
        )
    else:
        data = {"items": [], "totalItems": 0, "totalPages": 0}

    st["libros"] = {}
    items = []

    for b in data.get("items", []):
        key = uuid.uuid4().hex[:8]
        display = f"📕 {b['title']}"
        st["libros"][key] = {
            "titulo": b["title"],
            "autor": b["author"],
            "descarga": b["filepath"],
            "portada": b.get("coverUrl", b.get("cover_medium") or b.get("cover_low")),
            "hash": b["book_hash"],
        }
        items.append({"key": key, "title": b["title"], "display": display})

    total_pages = data.get("totalPages", 1)
    reply_markup = BotKeyboards.books_list(
        items=items,
        origin_type=origin_type,
        filter_val=filter_val,
        page=page,
        total_pages=total_pages,
    )

    st["current_view"] = "books_list"
    title = "📚 Catálogo de Libros" if origin_type == "recent" else "📖 Libros"
    st["titulo"] = title

    text = f"<b>{title}</b>\n✨ Explorando {data.get('totalItems', 0)} libros disponibles (Pág. {page}/{total_pages})."

    if hasattr(update, "callback_query") and update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=get_thread_id(update),
        )


async def mostrar_autores_local(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 1,
    force_new: bool = False,
):
    """Muestra lista de autores locales paginada en formato Rich Message unificado."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)
    page_size = 10

    data = await LibraryService.get_authors(page=page, page_size=page_size)
    authors = data["items"]
    total = data["total"]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    st["current_view"] = "authors"
    st["prev_view_local"] = "main"
    st["titulo"] = "✍️ Autores"

    blocks = build_authors_rich_blocks(
        authors=authors,
        total_authors=total,
        page=page,
        total_pages=total_pages,
    )

    if update.callback_query and not force_new:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            if res_edit and res_edit.get("ok"):
                return
        except Exception as e:
            logger.debug(f"[mostrar_autores_local] Falló edit_rich_message: {e}")

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )

    if not res or not res.get("ok"):
        reply_markup = BotKeyboards.authors_list(
            authors=authors, page=page, total_pages=total_pages
        )
        text = f"<b>✍️ Selecciona un Autor:</b>\nMostrando {len(authors)} autores (Pág. {page}/{total_pages})."
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )


def build_search_prompt_blocks() -> list[dict]:
    return build_search_prompt_rich_blocks()


async def pedir_termino_busqueda(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra la tarjeta de búsqueda interactiva en formato Rich Message."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)

    st["esperando_busqueda"] = True
    st["current_view"] = "search_prompt"
    st["prev_view_local"] = "main"
    st["titulo"] = "🔍 Buscador"

    blocks = build_search_prompt_rich_blocks(include_buttons=True)

    if update.callback_query and not force_new:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            if res_edit and res_edit.get("ok"):
                st["search_prompt_msg_id"] = update.callback_query.message.message_id
                return
        except Exception as e:
            logger.debug(f"[pedir_termino_busqueda] Falló edit_rich_message: {e}")

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )

    if res and res.get("ok"):
        st["search_prompt_msg_id"] = res.get("result", {}).get("message_id")
    else:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        search_cancel_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🏠 Menú Principal", callback_data="volver_menu"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cerrar"),
            ]
        ])
        text = (
            "🔍 <b>Buscador ZeePubs</b>\n\n"
            "¿Qué novela ligera estás buscando?\n"
            "<i>Escribe el título, autor o palabra clave a continuación:</i>"
        )
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=search_cancel_kb,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )
        if msg:
            st["search_prompt_msg_id"] = msg.message_id


async def mostrar_resultados_locales(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    query: str,
    series: list,
    books_standalone: list = None,
):
    """Muestra los resultados de una búsqueda local agrupada por series en formato Rich Message unificado."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)

    st["libros"] = {}
    st["colecciones"] = {}
    series_items = []

    # 1. Agregar Series (Resultados agrupados)
    found_series_hashes = set()
    if series:
        for i, s in enumerate(series):
            if i >= 10:
                break
            s_hash = s.get("series_hash") or s.get("id")
            if s_hash:
                found_series_hashes.add(s_hash)
            href = f"local_series|{s_hash}"
            series_title = (
                s.get("series_english")
                or s.get("name_english")
                or s.get("name")
                or s.get("series_name")
                or s.get("title", "Novela")
            )
            st["colecciones"][i] = {"titulo": series_title, "href": href}
            series_items.append({
                "title": series_title,
                "index": i,
                "book_count": s.get("book_count") or 1,
            })

    # 2. Agregar Libros "Sueltos"
    books_items = []
    if books_standalone:
        for b in books_standalone:
            b_s_hash = b.get("series_hash") or b.get("series_id")
            if b_s_hash and b_s_hash in found_series_hashes:
                continue
            if len(books_items) >= 6:
                break
            key = uuid.uuid4().hex[:8]

            eng_t = b.get("english_title") or b.get("series_english")
            if eng_t:
                vol_num = b.get("volume")
                if vol_num and vol_num > 0:
                    vol_str = f" {int(vol_num)}" if vol_num % 1 == 0 else f" {vol_num}"
                    display_title = f"{eng_t} - Volumen {vol_str}"
                else:
                    display_title = eng_t
            else:
                display_title = b.get("title", "Libro")

            display = f"📕 {display_title}"
            st["libros"][key] = {
                "titulo": display_title,
                "autor": b.get("author"),
                "descarga": b.get("filepath"),
                "portada": b.get("cover_medium") or b.get("cover_low"),
                "hash": b.get("book_hash") or b.get("id"),
            }
            books_items.append({"key": key, "title": display_title, "display": display})

    st["current_view"] = "search_results"
    st["titulo"] = f"🔍 Resultado: {query}"

    blocks = build_search_results_rich_blocks(
        query=query,
        series_results=series_items,
        standalone_books=books_items,
    )

    if hasattr(update, "callback_query") and update.callback_query:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            if res_edit and res_edit.get("ok"):
                return
        except Exception as e:
            logger.debug(f"[mostrar_resultados_locales] Falló edit_rich_message: {e}")

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )

    if not res or not res.get("ok"):
        reply_markup = BotKeyboards.search_results(
            series_items=series_items, books_items=books_items
        )
        total_s = len(series_items)
        total_b = len(books_items)
        if total_s > 0 or total_b > 0:
            text = f"<b>🔍 Resultados para:</b> {query}\n"
            if total_s > 0:
                text += f"📂 Encontradas <b>{total_s}</b> series.\n"
            if total_b > 0:
                text += f"📕 Encontrados <b>{total_b}</b> libros individuales.\n"
        else:
            text = f"❌ No se han encontrado resultados para: <b>{query}</b>"

        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            message_thread_id=thread_id,
        )

