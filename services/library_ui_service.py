import io
import logging
import os
import re
import uuid

from telegram import Update
from telegram.ext import ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.cover_service import resolve_cover_data, send_photo_bytes
from services.keyboard_factory import BotKeyboards
from services.library_service import LibraryService
from services.metadata_orchestrator.metadata_service import metadata_orchestrator
from services.rich_message_service import RichMessageService
from utils.download_limiter import downloads_left
from utils.helpers import (
    format_genre_chips,
    get_thread_id,
    get_translator_acronym,
    normalize_demography,
    resolve_title_cascade,
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


def build_main_menu_rich_blocks(
    user_name: str,
    stats: dict,
    downloads_str: str,
    user_rank: str,
    webapp_url: str | None = None,
    show_webapp: bool = False,
) -> list[dict]:
    """Construye la estructura de bloques nativos (Rich Blocks) para el Menú Principal."""
    series_cnt = stats.get("series_count", 0)
    books_cnt = stats.get("books_count", 0)

    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": "🌟 ZeePubs • Biblioteca Digital",
        },
        {
            "type": "paragraph",
            "text": [
                "¡Hola, ",
                {"type": "bold", "text": user_name},
                "! Bienvenido a tu portal de lectura de Novelas Ligeras en formato EPUB maquetado.",
            ],
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "📚 Series Disponibles", "align": "left"},
                    {"text": f"{series_cnt} series", "align": "left"},
                ],
                [
                    {"text": "📖 Volúmenes Indexados", "align": "left"},
                    {"text": f"{books_cnt} libros", "align": "left"},
                ],
                [
                    {"text": "📥 Cuota de Hoy", "align": "left"},
                    {"text": downloads_str, "align": "left"},
                ],
                [
                    {"text": "👤 Rango", "align": "left"},
                    {"text": user_rank, "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "💡 Guía Rápida y Comandos",
            "is_open": False,
            "blocks": [
                {
                    "type": "paragraph",
                    "text": "• /search <título> - Buscar cualquier novela al instante\n• /catalogo - Ver todas las series de la colección\n• /menu o /start - Volver a este menú en cualquier momento",
                }
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "📖 Catálogo de Series", "callback_data": "nav_local|all_series"},
                {"text": "⭐ Novedades", "callback_data": "nav_local|newest"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🏷️ Géneros", "callback_data": "nav_local|genres"},
                {"text": "✍️ Autores", "callback_data": "nav_local|authors"},
            ],
        },
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🔍 Buscar Novela", "callback_data": "buscar"},
            ],
        },
    ]

    if show_webapp and webapp_url:
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "🌐 Abrir ZeePub Web", "url": webapp_url},
                    {"text": "❌ Salir", "callback_data": "salir"},
                ],
            }
        )
    else:
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "❌ Salir", "callback_data": "salir"},
                ],
            }
        )

    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #BibliotecaDigital"})

    return blocks


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

    # 1. Obtener estadísticas globales y cuota
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

    # 2. Construir Bloques Nativos (Rich Blocks)
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


def build_genres_rich_blocks(genres: list[str]) -> list[dict]:
    """Construye los bloques nativos para el Explorador de Géneros."""
    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": "🏷️ Explorador de Géneros",
        },
        {
            "type": "paragraph",
            "text": "Selecciona una categoría para descubrir todas las novelas ligeras disponibles en la biblioteca:",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "🏷️ Total Categorías", "align": "left"},
                    {"text": f"{len(genres)} géneros", "align": "left"},
                ],
                [
                    {"text": "🎯 Modo de Exploración", "align": "left"},
                    {"text": "Filtrado directo por tag", "align": "left"},
                ],
            ],
        },
    ]

    # Botones en pares (máx 16)
    for i in range(0, min(16, len(genres)), 2):
        row = [{"text": f"🏷️ {genres[i]}", "callback_data": f"gen|{genres[i]}"}]
        if i + 1 < len(genres):
            row.append(
                {"text": f"🏷️ {genres[i + 1]}", "callback_data": f"gen|{genres[i + 1]}"}
            )
        blocks.append({"type": "buttons", "align": "center", "buttons": row})

    # Barra de navegación Zero Dead-Ends
    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⬅️ Volver", "callback_data": "subir_nivel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Generos"})
    return blocks


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


def build_series_catalog_rich_blocks(
    title: str,
    items: list[dict],
    total_series: int,
    page: int,
    total_pages: int,
    origin_type: str,
    filter_val: str | None = None,
) -> list[dict]:
    """Construye los bloques nativos para el Catálogo de Series Paginado."""
    safe_filter = filter_val or ""
    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": title,
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "📚 Total Colección", "align": "left"},
                    {"text": f"{total_series} series", "align": "left"},
                ],
                [
                    {"text": "📄 Página Actual", "align": "left"},
                    {"text": f"{page} de {total_pages}", "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "📋 Series en esta página",
            "is_open": True,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_compact": True,
                    "cells": [
                        [
                            {"text": f"{i + 1}. {item.get('title', 'Novela')}", "align": "left"},
                            {"text": f"{item.get('book_count', 1)} vols", "align": "left"},
                        ]
                        for i, item in enumerate(items)
                    ]
                    if items
                    else [[{"text": "No se encontraron series en esta página", "align": "left"}]],
                }
            ],
        },
    ]

    # Botones individuales por cada serie (máx 6-8 por página)
    for item in items:
        s_title = item.get("title", "Novela")
        idx = item.get("index", 0)
        if len(s_title) > 34:
            s_title = s_title[:31] + "..."
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [{"text": f"📁 {s_title}", "callback_data": f"col|{idx}"}],
            }
        )

    # Fila de Paginación
    nav_row = []
    if page > 1:
        nav_row.append(
            {
                "text": "◀️ Ant.",
                "callback_data": f"nav_p|{origin_type}|{safe_filter}|{page - 1}",
            }
        )
    else:
        nav_row.append({"text": "⛔ 1", "callback_data": "noop"})

    nav_row.append(
        {"text": f"📄 {page}/{total_pages}", "callback_data": "noop"}
    )

    if page < total_pages:
        nav_row.append(
            {
                "text": "Sig. ▶️",
                "callback_data": f"nav_p|{origin_type}|{safe_filter}|{page + 1}",
            }
        )
    else:
        nav_row.append({"text": f"⛔ {total_pages}", "callback_data": "noop"})

    blocks.append({"type": "buttons", "align": "center", "buttons": nav_row})

    # Barra de navegación Zero Dead-Ends
    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⬅️ Volver", "callback_data": "subir_nivel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Catalogo"})
    return blocks


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


async def mostrar_volumenes_local(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    series_hash: str,
    selected_key: str | None = None,
    force_new: bool = False,
):
    """
    Muestra la serie directamente en formato Rich Message unificado con selector/carrusel
    de volúmenes interactivo embebido dentro de la misma tarjeta.
    """
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)

    # 1. Obtener volúmenes de la serie
    volumes = await LibraryService.get_series_volumes(series_hash)
    if not volumes:
        if update.callback_query:
            await update.callback_query.answer(
                "⚠️ No se encontraron volúmenes para esta serie.", show_alert=True
            )
        return

    meta_serie = await LibraryService.get_series_metadata(series_hash)
    series_name = meta_serie.series_name if meta_serie else "Serie"

    # Ordenar volúmenes numéricamente de menor a mayor
    def parse_vol_num(v):
        vol_raw = v.get("volume")
        try:
            return float(vol_raw) if vol_raw is not None and str(vol_raw).strip() != "" else 0.0
        except (ValueError, TypeError):
            return 999.0

    volumes.sort(key=parse_vol_num)

    # Re-poblar estado si cambió de serie, si no hay libros o si la llave seleccionada no pertenece a esta serie
    need_rebuild = (
        st.get("current_series_hash") != series_hash
        or not st.get("libros")
        or (selected_key and selected_key not in st.get("libros", {}))
    )

    if need_rebuild:
        prev_target_hash = None
        if selected_key and selected_key in st.get("libros", {}):
            prev_target_hash = st["libros"][selected_key].get("book_hash") or st["libros"][selected_key].get("id")
        elif selected_key:
            prev_target_hash = selected_key

        st["libros"] = {}
        matched_key = None

        for v in volumes:
            key = uuid.uuid4().hex[:8]
            vol = v.get("volume")
            if vol is None or str(vol).strip() == "":
                vol = 0
            try:
                f_vol = float(vol)
                vol_display = int(f_vol) if f_vol.is_integer() else f_vol
            except (ValueError, TypeError):
                vol_display = vol

            vol_str = "Volumen Único" if vol_display == 0 else f"Vol. {vol_display}"
            translator = v.get("translator")
            tr_acronym = v.get("translator_siglas") or get_translator_acronym(translator)
            is_color = v.get("color_mode") == "color"
            color_tag = " [🎨]" if is_color else ""
            display = f"📖 {vol_str} [{tr_acronym}]{color_tag}"
            v_hash = v.get("book_hash") or v.get("id") or v.get("hash")

            st["libros"][key] = {
                "key": key,
                "titulo": v.get("title", ""),
                "english_title": v.get("english_title") or v.get("title", ""),
                "japanese_title": v.get("japanese_title", ""),
                "spanish_title": v.get("spanish_title", ""),
                "autor": v.get("author", ""),
                "descarga": v.get("filepath", "N/A"),
                "portada": v.get("coverUrl", ""),
                "hash": v.get("book_hash", ""),
                "book_hash": v.get("book_hash", ""),
                "id": v.get("id"),
                "display": display,
                "series": series_name,
                "series_hash": series_hash,
                "volume": vol,
                "vol_display": vol_display,
                "translator": translator,
                "translator_siglas": tr_acronym,
                "color": is_color,
            }

            if prev_target_hash and (v_hash == prev_target_hash or key == prev_target_hash):
                matched_key = key

        if matched_key:
            selected_key = matched_key

    st["current_view"] = "volumes_local"
    st["current_series_hash"] = series_hash

    # 2. Determinar el volumen activo (por defecto el primero ordenado, o el seleccionado)
    if selected_key and selected_key in st["libros"]:
        active_key = selected_key
    else:
        active_key = list(st["libros"].keys())[0]

    active_book = st["libros"][active_key]

    # 3. Enriquecer metadata del volumen activo
    book_id = (
        active_book.get("book_hash")
        or active_book.get("id")
        or active_book.get("hash")
        or active_book.get("descarga")
    )
    if book_id:
        meta_enriched = await metadata_orchestrator.get_enriched_metadata(book_id)
        if meta_enriched:
            active_book.update(meta_enriched)

    # 4. Resolver portada del volumen activo
    cover_raw = (
        active_book.get("cover_high")
        or active_book.get("coverUrl")
        or active_book.get("cover_original")
        or active_book.get("cover_medium")
        or active_book.get("cover")
        or active_book.get("portada")
        or active_book.get("cover_image")
        or active_book.get("cover_path")
    )
    if not cover_raw and book_id:
        from utils.library_db import COVERS_DIR
        for ext in [
            f"{book_id}_high.jpg",
            f"{book_id}.jpg",
            f"{book_id}_cover.jpg",
            f"{book_id}_original.jpg",
        ]:
            cand = os.path.join(COVERS_DIR, ext)
            if os.path.exists(cand):
                cover_raw = cand
                break

    cover_data = await resolve_cover_data(cover_raw)
    files = None
    if cover_data:
        if isinstance(cover_data, bytes):
            files = {"tomozaki_cover": ("cover.jpg", cover_data, "image/jpeg")}
        elif isinstance(cover_data, str) and os.path.exists(cover_data):
            try:
                with open(cover_data, "rb") as f:
                    files = {"tomozaki_cover": ("cover.jpg", f.read(), "image/jpeg")}
            except Exception as e:
                logger.warning(f"Error al leer archivo de portada local: {e}")

    # 5. Construir selector de volúmenes si la serie tiene más de 1 volumen
    volume_rows = []
    if len(st["libros"]) > 1:
        current_row = []
        for k, bk in st["libros"].items():
            vol_disp = bk.get("vol_display", bk.get("volume", 0))
            label = f"🔘 Vol. {vol_disp}" if k == active_key else f"Vol. {vol_disp}"
            cb = "noop" if k == active_key else f"sel_vol|{k}"
            current_row.append({"text": label, "callback_data": cb})
            if len(current_row) == 4:
                volume_rows.append(current_row)
                current_row = []
        if current_row:
            volume_rows.append(current_row)

    # 6. Cuota y rol
    left = await downloads_left(uid)
    can_download = True if left == "ilimitadas" else (isinstance(left, int) and left > 0)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)
    series_hash_short = series_hash[:16] if series_hash else None

    # 7. Construir Bloques Nativos (Rich Blocks)
    rich_blocks = build_book_rich_blocks(
        active_book,
        has_cover=bool(files and "tomozaki_cover" in files),
        key=active_key,
        can_download=can_download,
        is_admin_or_staff=is_staff,
        series_hash_short=series_hash_short,
        volume_buttons=volume_rows if volume_rows else None,
        show_nav_buttons=True,
    )

    # 8. Enviar o editar in-place
    if update.callback_query and not force_new:
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=rich_blocks,
                files=files if files else None,
            )
            if res_edit and res_edit.get("ok"):
                return
        except Exception as e:
            logger.debug(f"[mostrar_volumenes_local] No se pudo editar in-place: {e}")

        # Si no se pudo editar (ej. el mensaje origen era texto normal del catálogo), lo eliminamos
        if update.callback_query.message:
            try:
                await update.callback_query.message.delete()
            except Exception:
                pass

    # Si no es callback, o force_new=True, o falló la edición:
    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=rich_blocks,
        files=files if files else None,
        message_thread_id=thread_id,
    )


async def mostrar_detalles_libro(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key: str
):
    """
    Muestra la ficha técnica del libro con el flujo de 3 mensajes: Portada, Sinopsis y Technical Info.
    Sigue el patrón Premium/Glassmorphism y sincroniza la cuota de descargas.
    """
    from services.cover_service import resolve_cover_data, send_photo_bytes
    from services.metadata_orchestrator.metadata_service import metadata_orchestrator
    from services.publisher.publisher_service import TelegramPublisherProvider
    from utils.download_limiter import downloads_left
    from utils.helpers import get_thread_id
    from utils.template_engine import apply_publication_template

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    # Actualizar vista actual
    st["current_view"] = "detalles_libro"

    libro_st = st.get("libros", {}).get(key)

    if not libro_st:
        logger.warning(f"Libro no encontrado en estado para key: {key}")
        if update.callback_query:
            await update.callback_query.answer(
                "⚠️ Información no disponible.", show_alert=True
            )
        return

    # 1. Obtener Metadata Enriquecida (incluye sinopsis y detalles técnicos)
    book_id = libro_st.get("hash") or libro_st.get("descarga")
    meta = await metadata_orchestrator.get_enriched_metadata(book_id)

    # Actualizar estado local con la data enriquecida
    st["libros"][key].update(meta)
    libro = st["libros"][key]

    # 2. Preparar Capciones usando el Publisher Provider oficial (Garantiza paridad bot/canal)
    # Parte 0: Portada/Principal, Parte 1: Sinopsis, Parte 2: Info técnica
    from repositories.publication_repository import pub_repo

    try:
        db_templates = await pub_repo.get_templates(platform="telegram")
        cover_t = next(
            (t for t in db_templates if (t.extra_config or {}).get("type") == "cover"),
            None,
        )
        synopsis_t = next(
            (
                t
                for t in db_templates
                if (t.extra_config or {}).get("type") == "synopsis"
            ),
            None,
        )
        info_t = next(
            (t for t in db_templates if (t.extra_config or {}).get("type") == "info"),
            None,
        )

        cover_content = (
            cover_t.content if cover_t else TelegramPublisherProvider.COVER_TEMPLATE
        )
        syn_content = (
            synopsis_t.content
            if synopsis_t
            else TelegramPublisherProvider.SYNOPSIS_TEMPLATE
        )
        info_content = (
            info_t.content if info_t else TelegramPublisherProvider.INFO_TEMPLATE
        )
    except Exception as e:
        logger.warning(
            f"Error cargando plantillas de base de datos en mostrar_detalles_libro: {e}"
        )
        cover_content = TelegramPublisherProvider.COVER_TEMPLATE
        syn_content = TelegramPublisherProvider.SYNOPSIS_TEMPLATE
        info_content = TelegramPublisherProvider.INFO_TEMPLATE

    templates = [
        cover_content,
        syn_content,
        info_content,
    ]

    # Fallback si no hay sinopsis
    if not libro.get("sinopsis") and libro.get("description"):
        libro["sinopsis"] = libro.get("description")

    # Si aún no hay sinopsis, la cubrimos
    if not libro.get("sinopsis"):
        libro["sinopsis"] = "Sin sinopsis disponible."

    # Mapeo manual para asegurar que todas las variables del template están presentes
    t_en, t_jp, t_es = resolve_title_cascade(libro)

    libro_map = libro.copy()
    libro_map.update(
        {
            "series_english": t_en,
            "romaji_title": t_jp or "",
            "romaji": t_jp or "",
            "series_spanish": t_es or "",
            "spanish_title": t_es or "",
            "slug": libro.get("slug") or "",
            "layout_by": libro.get("layout_by") or "Desconocido",
            "traductor": libro.get("translator") or "Desconocida",
            # Pasar como listas para que apply_publication_template los procese correctamente
            "tags": libro.get("tags", []),
            "demographics": libro.get("demographics", []),
            "tipo": libro.get("book_type") or "Novela",
        }
    )

    # Limpiamos HTML de las partes antes de enviar (Telegram es delicado)
    def sanitize_tg_html(t: str) -> str:
        if not t:
            return ""

        t = re.sub(r"<(/?p|/?div|/?h\d|/?span|/?a[^>]*)>", "\n", t, flags=re.IGNORECASE)
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
        t = re.sub(r"<hr\s*/?>", "\n---\n", t, flags=re.IGNORECASE)
        t = re.sub(r"\n{3,}", "\n\n", t).strip()
        return t

    part0 = sanitize_tg_html(apply_publication_template(templates[0], libro_map))
    part1 = sanitize_tg_html(apply_publication_template(templates[1], libro_map))
    part2 = sanitize_tg_html(apply_publication_template(templates[2], libro_map))

    # IMPORTANTE: El template INFO_TEMPLATE incluye {archivo} que se expande a __ATTACH_FILE_SIGNAL__
    # Para la visualización previa en el bot, lo eliminamos para que no ensucie el slug
    part2 = part2.replace("__ATTACH_FILE_SIGNAL__", "").strip()

    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)

    # 3. Limpiar Menú de Volúmenes (Efecto de transición al detalle)
    if update.callback_query:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass

    # 4. ENVIAR MENSAJES (Flujo solicitado: Portada -> Sinopsis -> Detalles)
    if "last_detalles_msg_ids" not in st:
        st["last_detalles_msg_ids"] = []

    # IMPORTANTE: No limpiamos la lista aquí para que los comandos /cancel o 'cerrar' puedan
    # encontrar el mensaje con botones y quitarlos sin borrar la info.
    if update.callback_query:
        # Notificar que se queda en espera de forma sutil
        await update.callback_query.answer(
            "📌 Ficha técnica fijada en el chat.", show_alert=False
        )

    # A. Resolver Portada y preparar multimedia para Rich HTML
    portada_raw = (
        libro.get("cover_high")
        or libro.get("cover_medium")
        or libro.get("cover_low")
        or libro.get("cover_original")
        or libro.get("portada")
    )
    portada = await resolve_cover_data(portada_raw)

    files = {}
    media = None

    if portada:
        if isinstance(portada, bytes):
            files["tomozaki_cover"] = ("cover.png", io.BytesIO(portada), "image/png")
            media = [
                {
                    "id": "tomozaki_cover",
                    "media": {"type": "photo", "media": "attach://tomozaki_cover"},
                }
            ]
        elif isinstance(portada, str) and os.path.exists(portada):
            try:
                with open(portada, "rb") as f:
                    file_bytes = f.read()
                files["tomozaki_cover"] = (
                    "cover.png",
                    io.BytesIO(file_bytes),
                    "image/png",
                )
                media = [
                    {
                        "id": "tomozaki_cover",
                        "media": {"type": "photo", "media": "attach://tomozaki_cover"},
                    }
                ]
            except Exception as ex:
                logger.error(f"[UI Service] Error leyendo archivo de portada: {ex}")

    # B. Preparar Botones e información técnica del usuario
    left = await downloads_left(uid)
    can_download = left == "ilimitadas" or (isinstance(left, int) and left > 0)
    left_str = (
        f"tienes {left} descargas restantes hoy"
        if isinstance(left, int)
        else "tienes descargas ilimitadas"
    )

def build_book_rich_html(
    libro: dict,
    has_cover: bool = True,
    include_download: bool = False,
    filename: str | None = None,
    series_hash_short: str | None = None,
) -> str:
    """Construye el HTML dinámico completo para el Rich Message del libro."""
    html_parts = []

    # 1. Imagen al inicio de todo
    if has_cover:
        html_parts.append('<img src="tg://photo?id=tomozaki_cover" />\n')

    # 2. Títulos en cascada
    title_en, title_jp, title_es = resolve_title_cascade(libro)
    html_parts.append(f"<h3>🇬🇧 {title_en}</h3>")
    if title_jp:
        html_parts.append(f"<h4>🇯🇵 {title_jp}</h4>")
    if title_es:
        html_parts.append(f"<h5>🇪🇸 {title_es}</h5>")

    volume = libro.get("volume")
    if volume:
        html_parts.append(f"<h6>📚 Volumen {volume}</h6>\n")

    # Géneros en chips / tags estilizados
    generos = libro.get("tags_json") or libro.get("tags") or libro.get("generos")
    chips_generos = format_genre_chips(generos)
    if chips_generos:
        html_parts.append(f"<p>🏷️ <i>{chips_generos}</i></p>\n")

    # 3. TABLA 1: Ficha artística y literaria
    tabla_literaria = (
        "<details open>\n"
        "  <summary>📋 Ficha Técnica</summary>\n"
        "  <table bordered striped compact>\n"
    )

    autor = libro.get("author") or libro.get("autor") or "Desconocido"
    tabla_literaria += f"    <tr><td><b>👤 Autor</b></td><td>{autor}</td></tr>\n"

    ilustrador = libro.get("illustrator") or libro.get("ilustrador")
    if ilustrador:
        ills = [
            i.strip()
            for i in re.split(r"[,;/+&]|\s+y\s+|\s+and\s+", str(ilustrador))
            if i.strip() and i.strip().upper() not in ("N/A", "DESCONOCIDO", "-")
        ]
        ill_val = ", ".join(ills) if len(ills) > 1 else str(ilustrador).strip()
        tabla_literaria += (
            f"    <tr><td><b>🎨 Ilustrador</b></td><td>{ill_val}</td></tr>\n"
        )

    layout_by = libro.get("layout_by") or libro.get("maquetador")
    if layout_by:
        maqs = [
            m.strip()
            for m in re.split(r"[,;]+|\s+(?=#)|\s+", str(layout_by))
            if m.strip()
        ]
        layout_val = " ".join(m if m.startswith("#") else f"#{m}" for m in maqs)
        tabla_literaria += (
            f"    <tr><td><b>💻 Maquetador</b></td><td>{layout_val}</td></tr>\n"
        )

    categoria = libro.get("book_type") or libro.get("tipo") or "Novela"
    tabla_literaria += f"    <tr><td><b>📦 Categoría</b></td><td>{categoria}</td></tr>\n"

    demo = (
        libro.get("demographics_json")
        or libro.get("demographics")
        or libro.get("demografia")
    )
    demo_val = normalize_demography(demo)
    if demo_val:
        tabla_literaria += (
            f"    <tr><td><b>👥 Demografía</b></td><td>{demo_val}</td></tr>\n"
        )

    traductor = libro.get("translator") or libro.get("traductor")
    if traductor:
        tabla_literaria += (
            f"    <tr><td><b>🌐 Traductor</b></td><td>{traductor}</td></tr>\n"
        )

    grupo_trad = (
        libro.get("publisher")
        or libro.get("translation_group")
        or libro.get("grupo_traductor")
    )
    if grupo_trad:
        grupo_trad_val = grupo_trad
        if libro.get("translation_group_url"):
            url_g = libro.get("translation_group_url")
            grupo_trad_val = f'<a href="{url_g}">{grupo_trad}</a>'
        tabla_literaria += (
            f"    <tr><td><b>🏢 Grupo Traductor</b></td><td>{grupo_trad_val}</td></tr>\n"
        )

    tabla_literaria += "  </table>\n</details>\n"
    html_parts.append(tabla_literaria)

    # 4. SINOPSIS: Acordeón colapsable
    sinopsis_raw = libro.get("sinopsis") or "Sin sinopsis disponible."
    html_parts.append(
        "<details>\n"
        "  <summary>📖 Ver Sinopsis</summary>\n"
        "  <blockquote>\n"
        f"    {sinopsis_raw}\n"
        "  </blockquote>\n"
        "</details>\n"
    )

    # 5. TABLA 2: Detalles del archivo
    size_val = libro.get("size")
    if not size_val and libro.get("file_size"):
        try:
            size_bytes = int(libro.get("file_size"))
            size_val = f"{size_bytes / (1024 * 1024):.2f} MB"
        except Exception:
            size_val = "Desconocido"
    if not size_val:
        size_val = "Desconocido"

    version_val = libro.get("epub_version") or libro.get("version") or "3.0"

    tabla_archivo = (
        "<details>\n"
        "  <summary>📂 Ver Detalles del Archivo</summary>\n"
        "  <table bordered striped compact>\n"
        f"    <tr><td><b>📂 Nombre</b></td><td>{libro.get('title') or 'Desconocido'}</td></tr>\n"
    )
    if volume:
        tabla_archivo += (
            f"    <tr><td><b>📖 Volumen</b></td><td>Volumen {volume}</td></tr>\n"
        )

    tabla_archivo += (
        f"    <tr><td><b>ℹ️ Versión Epub</b></td><td>{version_val}</td></tr>\n"
    )

    fecha = (
        libro.get("updated_at") or libro.get("actualizado") or libro.get("indexed_at")
    )
    if fecha:
        if hasattr(fecha, "strftime"):
            fecha_str = fecha.strftime("%d-%m-%Y")
        else:
            fecha_str = str(fecha)
        tabla_archivo += (
            f"    <tr><td><b>📅 Actualizado</b></td><td>{fecha_str}</td></tr>\n"
        )

    tabla_archivo += f"    <tr><td><b>💾 Tamaño</b></td><td>{size_val}</td></tr>\n"

    tabla_archivo += "  </table>\n</details>\n"
    html_parts.append(tabla_archivo)

    # 6. Si se incluye descarga embebida
    if include_download:
        html_parts.append(
            "<details open>\n"
            "  <summary>📥 Descargar EPUB</summary>\n"
            '  <tg-document src="tg://document?id=epub_file" />\n'
            "</details>\n"
        )

    # 7. Línea divisoria y pie con margen no recortable
    html_parts.append("<hr/>")

    slug = libro.get("slug")
    if slug:
        hashtag_serie = slug if slug.startswith("#") else f"#{slug}"
    else:
        clean_title = re.sub(r"[^\w\s]", "", title_en).replace(" ", "_")
        hashtag_serie = f"#{clean_title}"

    html_parts.append(f"<p>{hashtag_serie}</p>")
    html_parts.append("<p>⠀</p>")

    return "\n".join(html_parts)


def build_book_rich_blocks(
    libro: dict,
    has_cover: bool = True,
    include_download: bool = False,
    key: str | None = None,
    can_download: bool = True,
    is_admin_or_staff: bool = False,
    series_hash_short: str | None = None,
    volume_buttons: list[list[dict]] | None = None,
    show_nav_buttons: bool = True,
) -> list[dict]:
    """Construye la estructura de bloques nativos (Rich Blocks) para Telegram Bot API."""
    blocks = []

    # 1. Portada
    if has_cover:
        blocks.append(
            {
                "type": "photo",
                "photo": {
                    "type": "photo",
                    "media": "attach://tomozaki_cover",
                },
            }
        )

    # 2. Títulos en cascada
    title_en, title_jp, title_es = resolve_title_cascade(libro)
    blocks.append(
        {
            "type": "heading",
            "size": 3,
            "text": f"🇬🇧 {title_en}",
        }
    )
    if title_jp:
        blocks.append(
            {
                "type": "heading",
                "size": 4,
                "text": f"🇯🇵 {title_jp}",
            }
        )
    if title_es:
        blocks.append(
            {
                "type": "heading",
                "size": 5,
                "text": f"🇪🇸 {title_es}",
            }
        )

    volume = libro.get("volume")
    if volume:
        blocks.append(
            {
                "type": "heading",
                "size": 6,
                "text": f"📚 Volumen {volume}",
            }
        )

    # Géneros
    generos = libro.get("tags_json") or libro.get("tags") or libro.get("generos")
    chips_generos = format_genre_chips(generos)
    if chips_generos:
        blocks.append(
            {
                "type": "paragraph",
                "text": f"🏷️ {chips_generos}",
            }
        )

    # 3. TABLA 1: Ficha Artística
    tabla_cells = []
    autor = libro.get("author") or libro.get("autor") or "Desconocido"
    tabla_cells.append([{"text": "👤 Autor"}, {"text": autor}])

    ilustrador = libro.get("illustrator") or libro.get("ilustrador")
    if ilustrador:
        ills = [
            i.strip()
            for i in re.split(r"[,;/+&]|\s+y\s+|\s+and\s+", str(ilustrador))
            if i.strip() and i.strip().upper() not in ("N/A", "DESCONOCIDO", "-")
        ]
        ill_val = ", ".join(ills) if len(ills) > 1 else str(ilustrador).strip()
        tabla_cells.append([{"text": "🎨 Ilustrador"}, {"text": ill_val}])

    layout_by = libro.get("layout_by") or libro.get("maquetador")
    if layout_by:
        maqs = [
            m.strip()
            for m in re.split(r"[,;/+&]|\s+y\s+|\s+and\s+", str(layout_by))
            if m.strip() and m.strip().upper() not in ("N/A", "DESCONOCIDO", "-")
        ]
        maq_tags = [m if m.startswith("#") else f"#{m}" for m in maqs]
        maq_val = (
            " ".join(maq_tags)
            if len(maq_tags) > 1
            else (maq_tags[0] if maq_tags else "")
        )
        if maq_val:
            tabla_cells.append([{"text": "📓 Maquetador"}, {"text": maq_val}])

    cat_val = libro.get("book_type") or libro.get("categoria") or "Novela Ligera"
    tabla_cells.append([{"text": "📦 Categoría"}, {"text": cat_val}])

    demografia = normalize_demography(
        libro.get("demographics") or libro.get("demografia")
    )
    if demografia:
        tabla_cells.append([{"text": "👥 Demografía"}, {"text": demografia}])

    traductor = libro.get("translator") or libro.get("traductor")
    if traductor:
        tabla_cells.append([{"text": "🌐 Traductor"}, {"text": str(traductor)}])

    grupo_tr = (
        libro.get("group") or libro.get("publisher") or libro.get("editorial")
    )
    if grupo_tr:
        tabla_cells.append([{"text": "🏢 Grupo Traductor"}, {"text": str(grupo_tr)}])

    blocks.append(
        {
            "type": "details",
            "summary": "📋 Ficha Técnica",
            "is_open": True,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_striped": True,
                    "is_compact": True,
                    "cells": tabla_cells,
                }
            ],
        }
    )

    # 4. TABLA 2: Sinopsis en Details
    sinopsis = libro.get("sinopsis") or libro.get("description")
    if sinopsis:
        sinopsis_clean = re.sub(r"<[^>]+>", "", str(sinopsis)).strip()
        if len(sinopsis_clean) > 800:
            sinopsis_clean = sinopsis_clean[:790] + "..."
        blocks.append(
            {
                "type": "details",
                "summary": "📖 Ver Sinopsis",
                "is_open": False,
                "blocks": [
                    {
                        "type": "blockquote",
                        "blocks": [
                            {
                                "type": "paragraph",
                                "text": sinopsis_clean,
                            }
                        ],
                    }
                ],
            }
        )

    # 5. TABLA 3: Detalles Técnicos del Archivo
    tech_cells = []
    formato = libro.get("epub_version") or "EPUB 3.0"
    tech_cells.append([{"text": "📄 Formato"}, {"text": formato}])

    raw_pages = libro.get("page_count")
    if raw_pages and str(raw_pages).isdigit() and int(raw_pages) > 0:
        tech_cells.append([{"text": "📑 Páginas"}, {"text": f"~{raw_pages} págs"}])

    raw_words = libro.get("word_count")
    if raw_words and str(raw_words).isdigit() and int(raw_words) > 0:
        tech_cells.append(
            [{"text": "📝 Palabras"}, {"text": f"{int(raw_words):,} palabras"}]
        )

    reading_time = libro.get("reading_time")
    if reading_time and str(reading_time).isdigit() and int(reading_time) > 0:
        mins = int(reading_time)
        hrs = mins // 60
        rem_mins = mins % 60
        time_str = f"{hrs}h {rem_mins}m" if hrs > 0 else f"{mins}m"
        tech_cells.append([{"text": "⏱️ Lectura"}, {"text": time_str}])

    fecha = (
        libro.get("modified_at_opf")
        or libro.get("published_at")
        or libro.get("modifiedAt")
        or libro.get("updated_at")
    )
    if fecha:
        if hasattr(fecha, "strftime"):
            fecha_str = fecha.strftime("%d-%m-%Y")
        else:
            fecha_str = str(fecha)
        tech_cells.append([{"text": "📅 Actualizado"}, {"text": fecha_str}])

    raw_size = libro.get("file_size") or libro.get("size")
    if raw_size:
        try:
            size_num = float(raw_size)
            if size_num >= 1024 * 1024:
                size_val = f"{size_num / (1024 * 1024):.1f} MB"
            elif size_num >= 1024:
                size_val = f"{size_num / 1024:.1f} KB"
            else:
                size_val = f"{int(size_num)} B"
        except (ValueError, TypeError):
            size_val = str(raw_size)
    else:
        size_val = "N/A"
    tech_cells.append([{"text": "💾 Tamaño"}, {"text": size_val}])

    blocks.append(
        {
            "type": "details",
            "summary": "📁 Ver Detalles del Archivo",
            "is_open": False,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_compact": True,
                    "cells": tech_cells,
                }
            ],
        }
    )

    # 6. Selector de Volúmenes (si hay botones de volumen)
    if volume_buttons:
        for row in volume_buttons:
            if row:
                blocks.append(
                    {
                        "type": "buttons",
                        "align": "center",
                        "buttons": row,
                    }
                )

    # 7. Si se incluye descarga embebida
    if include_download:
        blocks.append(
            {
                "type": "details",
                "summary": "📥 Descargar EPUB",
                "is_open": True,
                "blocks": [
                    {
                        "type": "document",
                        "document": {
                            "type": "document",
                            "media": "attach://epub_file",
                        },
                    }
                ],
            }
        )
    elif key:
        # Botón Descargar Incrustado en el Rich Message
        btn_text = (
            "📥 Descargar EPUB"
            if can_download
            else "⛔ Sin descargas disponibles"
        )
        cb_data = f"dl_confirm|{key}" if can_download else "noop"
        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {
                        "text": btn_text,
                        "callback_data": cb_data,
                    }
                ],
            }
        )
        if is_admin_or_staff:
            blocks.append(
                {
                    "type": "buttons",
                    "align": "center",
                    "buttons": [
                        {
                            "text": "📢 Publicar en Telegram",
                            "callback_data": f"pub_channel|{key}",
                        }
                    ],
                }
            )

    # 8. Botones de navegación incrustados
    if show_nav_buttons:
        nav_row = [
            {"text": "⬅️ Volver", "callback_data": "nav_back"},
            {"text": "📚 Catálogo", "callback_data": "nav_local|all_series"},
            {"text": "🏠 Inicio", "callback_data": "main_menu"},
            {"text": "❌ Salir", "callback_data": "salir"},
        ]

        blocks.append(
            {
                "type": "buttons",
                "align": "center",
                "buttons": nav_row,
            }
        )

    # 9. Divider y pie con hashtag
    blocks.append({"type": "divider"})
    slug = libro.get("slug")
    if slug:
        hashtag_serie = slug if slug.startswith("#") else f"#{slug}"
    else:
        clean_title = re.sub(r"[^\w\s]", "", title_en).replace(" ", "_")
        hashtag_serie = f"#{clean_title}"

    blocks.append({"type": "paragraph", "text": hashtag_serie})

    return blocks


async def mostrar_detalles_libro(
    update: Update, context: ContextTypes.DEFAULT_TYPE, key: str
):
    """Muestra la ficha técnica y opciones para un libro específico."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)
    st.setdefault("last_detalles_msg_ids", [])
    libro_st = st.get("libros", {}).get(key)

    if not libro_st:
        logger.warning(f"Libro no encontrado en estado para key: {key}")
        if update.callback_query:
            await update.callback_query.answer(
                "⚠️ Información no disponible.", show_alert=True
            )
        return

    # 1. Obtener Metadata Enriquecida (incluye sinopsis y detalles técnicos)
    book_id = (
        libro_st.get("book_hash")
        or libro_st.get("id")
        or libro_st.get("hash")
        or libro_st.get("descarga")
    )
    meta = await metadata_orchestrator.get_enriched_metadata(book_id)

    # Actualizar estado local con la data enriquecida
    st["libros"][key].update(meta)
    libro = st["libros"][key]

    # Si el libro pertenece a una serie, mostrarlo directamente en el carrusel de volúmenes
    series_hash = libro.get("series_hash") or meta.get("series_hash") or st.get("current_series_hash")
    if series_hash:
        return await mostrar_volumenes_local(
            update,
            context,
            series_hash=series_hash,
            selected_key=key,
            force_new=False,
        )

    # Preparar Portada y Archivos
    cover_raw = (
        libro.get("cover_high")
        or libro.get("coverUrl")
        or libro.get("cover_original")
        or libro.get("cover_medium")
        or libro.get("cover")
        or libro.get("portada")
        or libro.get("cover_image")
        or libro.get("cover_path")
    )
    if not cover_raw and book_id:
        from utils.library_db import COVERS_DIR

        for ext in [
            f"{book_id}_high.jpg",
            f"{book_id}.jpg",
            f"{book_id}_cover.jpg",
            f"{book_id}_original.jpg",
        ]:
            cand = os.path.join(COVERS_DIR, ext)
            if os.path.exists(cand):
                cover_raw = cand
                break

    cover_data = await resolve_cover_data(cover_raw)
    files = None

    if cover_data:
        if isinstance(cover_data, bytes):
            files = {
                "tomozaki_cover": ("cover.jpg", cover_data, "image/jpeg")
            }
        elif isinstance(cover_data, str) and os.path.exists(cover_data):
            try:
                with open(cover_data, "rb") as f:
                    files = {
                        "tomozaki_cover": ("cover.jpg", f.read(), "image/jpeg")
                    }
            except Exception as e:
                logger.warning(f"Error al leer archivo de portada local: {e}")

    # Verificar cuota de descarga y rol
    left = await downloads_left(uid)
    can_download = (
        True
        if left == "ilimitadas"
        else (isinstance(left, int) and left > 0)
    )
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)
    series_hash = st.get("current_series_hash") or libro.get("series_hash")
    series_hash_short = series_hash[:16] if series_hash else None

    # C. Construir Bloques Nativos (Rich Blocks) con botones incrustados
    rich_blocks = build_book_rich_blocks(
        libro,
        has_cover=bool(files and "tomozaki_cover" in files),
        key=key,
        can_download=can_download,
        is_admin_or_staff=is_staff,
        series_hash_short=series_hash_short,
    )

    # D. Intentar enviar Rich Message unificado usando Bloques Nativos
    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=rich_blocks,
        files=files if files else None,
        message_thread_id=thread_id,
    )

    # E. Fallback tradicional si la API de Telegram o el transporte fallan
    if not res or not res.get("ok"):
        logger.warning(
            "[UI Service] Fallback a mensaje tradicional en mostrar_detalles_libro"
        )
        reply_markup = BotKeyboards.book_details(
            key=key, is_admin_or_staff=is_staff, can_download=can_download
        )
        html_content = build_book_rich_html(
            libro, has_cover=bool(files and "tomozaki_cover" in files)
        )
        res_html = await RichMessageService.send_rich_message(
            chat_id=chat_id,
            html=html_content,
            files=files if files else None,
            reply_markup=reply_markup,
            message_thread_id=thread_id,
        )
        if not res_html or not res_html.get("ok"):
            title_en, title_jp, title_es = resolve_title_cascade(libro)
            desc_txt = f"📖 <b>{title_en}</b>"
            if libro.get("volume"):
                desc_txt += f" - Vol. {libro.get('volume')}"
            sinopsis = libro.get("sinopsis") or "Sin sinopsis disponible."

            fallback_text = f"{desc_txt}\n\n{sinopsis}"
            if len(fallback_text) > 4000:
                fallback_text = fallback_text[:3990] + "..."

            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=fallback_text,
                reply_markup=reply_markup,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            if msg:
                st["last_detalles_msg_ids"].append(msg.message_id)
        elif res_html.get("result", {}).get("message_id"):
            st["last_detalles_msg_ids"].append(
                res_html["result"]["message_id"]
            )
    else:
        # Si fue exitoso el Rich Message, guardamos su ID de mensaje para limpieza
        rich_msg_id = res.get("result", {}).get("message_id")
        if rich_msg_id:
            st["last_detalles_msg_ids"].append(rich_msg_id)


def build_authors_rich_blocks(
    authors: list[str],
    total_authors: int,
    page: int,
    total_pages: int,
) -> list[dict]:
    """Construye los bloques nativos para el Directorio de Autores."""
    blocks = [
        {
            "type": "heading",
            "size": 2,
            "text": "✍️ Directorio de Autores",
        },
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [
                    {"text": "✍️ Total Autores", "align": "left"},
                    {"text": f"{total_authors} autores", "align": "left"},
                ],
                [
                    {"text": "📄 Página Actual", "align": "left"},
                    {"text": f"{page} de {total_pages}", "align": "left"},
                ],
            ],
        },
        {
            "type": "details",
            "summary": "📋 Autores en esta página",
            "is_open": True,
            "blocks": [
                {
                    "type": "table",
                    "is_bordered": True,
                    "is_compact": True,
                    "cells": [
                        [
                            {"text": f"{i + 1}. {a}", "align": "left"},
                            {"text": "Autor", "align": "left"},
                        ]
                        for i, a in enumerate(authors)
                    ]
                    if authors
                    else [[{"text": "No se encontraron autores en esta página", "align": "left"}]],
                }
            ],
        },
    ]

    # Botones individuales por autor (en pares o individuales)
    for i in range(0, len(authors), 2):
        row = [{"text": f"✍️ {authors[i]}", "callback_data": f"aut|{authors[i]}"}]
        if i + 1 < len(authors):
            row.append(
                {"text": f"✍️ {authors[i + 1]}", "callback_data": f"aut|{authors[i + 1]}"}
            )
        blocks.append({"type": "buttons", "align": "center", "buttons": row})

    # Paginación
    nav_row = []
    if page > 1:
        nav_row.append(
            {
                "text": "◀️ Ant.",
                "callback_data": f"nav_aut|{page - 1}",
            }
        )
    else:
        nav_row.append({"text": "⛔ 1", "callback_data": "noop"})

    nav_row.append(
        {"text": f"📄 {page}/{total_pages}", "callback_data": "noop"}
    )

    if page < total_pages:
        nav_row.append(
            {
                "text": "Sig. ▶️",
                "callback_data": f"nav_aut|{page + 1}",
            }
        )
    else:
        nav_row.append({"text": f"⛔ {total_pages}", "callback_data": "noop"})

    blocks.append({"type": "buttons", "align": "center", "buttons": nav_row})

    # Barra de navegación Zero Dead-Ends
    blocks.append(
        {
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "⬅️ Volver", "callback_data": "subir_nivel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                {"text": "❌ Salir", "callback_data": "salir"},
            ],
        }
    )
    blocks.append({"type": "divider"})
    blocks.append({"type": "paragraph", "text": "#ZeePubs #Autores"})
    return blocks


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
    series_items = []

    # 1. Agregar Series (Resultados agrupados)
    if series:
        for i, s in enumerate(series):
            if i >= 15:
                break
            href = f"local_series|{s['series_hash']}"
            series_title = (
                s.get("series_english")
                or s.get("name_english")
                or s.get("name")
                or s.get("series_name")
                or s.get("title", "Novela")
            )
            st["colecciones"][i] = {"titulo": series_title, "href": href}
            series_items.append({"title": series_title, "index": i})

    # 2. Agregar Libros "Sueltos" (que no pertenecen a las series encontradas o no tienen serie)
    books_items = []
    if books_standalone:
        for b in books_standalone:
            if len(books_items) >= 15:
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
                display_title = b["title"]

            display = f"📕 {display_title}"
            st["libros"][key] = {
                "titulo": display_title,
                "autor": b["author"],
                "descarga": b["filepath"],
                "portada": b.get("cover_medium") or b.get("cover_low"),
                "hash": b["book_hash"],
            }
            books_items.append({"key": key, "title": display_title, "display": display})

    reply_markup = BotKeyboards.search_results(
        series_items=series_items, books_items=books_items
    )

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
