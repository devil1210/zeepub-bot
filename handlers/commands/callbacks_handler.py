import io
import logging
import os
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from handlers.commands.base_handler import BaseCommandHandler
from services.keyboard_factory import BotKeyboards
from services.library_service import LibraryService
from services.library_ui_service import (
    build_book_rich_blocks,
    build_book_rich_html,
    mostrar_menu_principal,
    mostrar_generos,
    mostrar_series,
    mostrar_libros,
    mostrar_volumenes_local,
    mostrar_detalles_libro,
    mostrar_autores_local,
)
from services.download_history import register_book_download
from services.cover_service import resolve_cover_data, send_doc_bytes
from services.rich_message_service import RichMessageService
from utils.download_limiter import downloads_left
from utils.helpers import format_genre_chips, get_thread_id

logger = logging.getLogger(__name__)


class CallbackHandlerV6(BaseCommandHandler):
    """
    Centralized handler for Telegram Callback Queries in the v6 architecture.
    Bridges the gap between the premium library UI and async services.
    """

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)

        msg_id = query.message.message_id if query.message else None
        is_downloaded_msg = bool(msg_id and msg_id in st.get("downloaded_msgs", set()))

        # Si el usuario interactúa desde un mensaje que contiene un libro descargado,
        # limpiamos sus botones de navegación para preservarlo intacto en el chat.
        if is_downloaded_msg:
            down_data = st.get("libros_downloaded", {}).pop(msg_id, {})
            dl_libro = down_data.get("libro") or {}
            dl_files = down_data.get("files")
            if dl_libro:
                clean_blocks = build_book_rich_blocks(
                    dl_libro,
                    has_cover=bool(dl_files and "tomozaki_cover" in dl_files),
                    include_download=True,
                    volume_buttons=None,
                    show_nav_buttons=False,
                )
                try:
                    await RichMessageService.edit_rich_message(
                        chat_id=update.effective_chat.id,
                        message_id=msg_id,
                        blocks=clean_blocks,
                        files=dl_files if dl_files else None,
                    )
                except Exception as e:
                    logger.warning(f"Error limpiando botones de mensaje descargado: {e}")
            st["downloaded_msgs"].discard(msg_id)

            # Si pulsó Salir en el mensaje descargado, simplemente confirmamos y no enviamos nada nuevo
            if data == "noop":
                try:
                    await query.answer("¡Lectura guardada! 📚", show_alert=False)
                except Exception:
                    pass
                return

        # 1. Always answer callback to prevent Telegram client from spinning
        try:
            await query.answer()
        except Exception:
            pass

        # Ignore no-op pagination buttons
        if data == "noop":
            return

        force_new = is_downloaded_msg

        try:
            # 1. Main Menu Navigation
            if data == "main_menu" or data == "volver_menu":
                await mostrar_menu_principal(update, context, force_new=force_new)

            # 2. Categorized Lists Navigation
            elif data.startswith("nav_local|"):
                category = data.split("|")[1]
                if category == "all_series":
                    await mostrar_series(
                        update, context, origin_type="all_series", page=1, force_new=force_new
                    )
                elif category == "newest":
                    await mostrar_series(update, context, origin_type="newest", page=1, force_new=force_new)
                elif category == "genres":
                    await mostrar_generos(update, context, force_new=force_new)
                elif category == "authors":
                    await mostrar_autores_local(update, context, page=1, force_new=force_new)

            # 4. Genre Filtering
            elif data.startswith("gen|"):
                genre_name = data.split("|")[1]
                await mostrar_series(
                    update, context, origin_type="genre", filter_val=genre_name, page=1
                )

            # 5. Author Filtering
            elif data.startswith("aut|"):
                author_name = data.split("|")[1]
                await mostrar_series(
                    update,
                    context,
                    origin_type="author",
                    filter_val=author_name,
                    page=1,
                )

            # 6. Series Paginator
            elif data.startswith("nav_p|"):
                parts = data.split("|")
                origin_type = parts[1]
                filter_val = parts[2] if parts[2] else None
                page = int(parts[3])
                await mostrar_series(
                    update,
                    context,
                    origin_type=origin_type,
                    filter_val=filter_val,
                    page=page,
                )

            # 7. Books Paginator
            elif data.startswith("nav_b|"):
                parts = data.split("|")
                origin_type = parts[1]
                filter_val = parts[2] if parts[2] else None
                page = int(parts[3])
                await mostrar_libros(
                    update,
                    context,
                    origin_type=origin_type,
                    filter_val=filter_val,
                    page=page,
                )

            # 8. Authors Paginator
            elif data.startswith("nav_au|"):
                page = int(data.split("|")[1])
                await mostrar_autores_local(update, context, page=page)

            # 9. Choose Series (Show Volumes)
            elif data.startswith("col|"):
                index = int(data.split("|")[1])
                col_info = st.get("colecciones", {}).get(index)
                if col_info and "href" in col_info:
                    href = col_info["href"]
                    series_hash = href.split("|")[1]
                    # Guardamos historial para permitir navegación "Volver"
                    st["historial"] = st.get("historial", [])
                    st["historial"].append(
                        (
                            "series_list",
                            st.get("origin_type"),
                            st.get("filter_val"),
                            st.get("current_page"),
                        )
                    )
                    await mostrar_volumenes_local(
                        update, context, series_hash, force_new=force_new
                    )
                else:
                    await query.answer("⚠️ Serie no disponible.", show_alert=True)

            # Direct Navigation to Series Volumes
            elif data.startswith("show_series|"):
                series_hash_short = data.split("|")[1]
                series_hash = await LibraryService.resolve_series_hash(
                    series_hash_short
                )
                await mostrar_volumenes_local(
                    update, context, series_hash, force_new=True
                )

            # Volume Selector In-Place Switcher
            elif data.startswith("sel_vol|"):
                key = data.split("|")[1]
                series_hash = st.get("current_series_hash") or (
                    st.get("libros", {}).get(key, {}).get("series_hash")
                )
                if series_hash:
                    await mostrar_volumenes_local(
                        update,
                        context,
                        series_hash=series_hash,
                        selected_key=key,
                        force_new=force_new,
                    )

            # 10. Choose Book (Show Rich Metadata details)
            elif data.startswith("lib|"):
                key = data.split("|")[1]
                series_hash = st.get("current_series_hash")
                if series_hash:
                    await mostrar_volumenes_local(
                        update,
                        context,
                        series_hash=series_hash,
                        selected_key=key,
                        force_new=force_new,
                    )
                else:
                    await mostrar_detalles_libro(update, context, key)

            # 11. Book Download Direct Action
            elif data.startswith("dl_confirm|"):
                key = data.split("|")[1]
                libro_st = st.get("libros", {}).get(key)

                if not libro_st:
                    await query.answer(
                        "⚠️ Información no encontrada. Intenta buscar la novela de nuevo.",
                        show_alert=True,
                    )
                    return

                filepath = libro_st.get("descarga")
                title = libro_st.get("titulo", "novela")
                book_hash = libro_st.get("hash")

                # A. Validate quota limits
                left = await downloads_left(uid)
                if left != "ilimitadas" and isinstance(left, int) and left <= 0:
                    await query.answer(
                        "⛔ Límite alcanzado. Te has quedado sin descargas para hoy.",
                        show_alert=True,
                    )
                    return

                await query.answer(
                    "⚡️ Descargando e iniciando envío...", show_alert=False
                )

                # C. Formatear pie de foto (caption) del archivo (únicamente el slug)
                slug = libro_st.get("slug") or ""
                if slug:
                    caption = slug if slug.startswith("#") else f"#{slug}"
                else:
                    clean_title = re.sub(r"[^\w\s]", "", title).replace(" ", "_")
                    caption = f"#{clean_title}"

                try:
                    # D. Construir y editar el Rich Message existente in-place agregándole la descarga
                    filename = libro_st.get("filename") or f"{title}.epub"
                    series_hash = st.get("current_series_hash")
                    series_hash_short = series_hash[:16] if series_hash else None
                    post_keyboard = BotKeyboards.post_download(series_hash_short)

                    # 1. Resolver portada
                    b_id = (
                        libro_st.get("book_hash")
                        or libro_st.get("id")
                        or libro_st.get("hash")
                        or st.get("current_series_hash")
                    )
                    cover_raw = (
                        libro_st.get("cover_high")
                        or libro_st.get("coverUrl")
                        or libro_st.get("cover_original")
                        or libro_st.get("cover_medium")
                        or libro_st.get("cover")
                        or libro_st.get("portada")
                        or libro_st.get("cover_image")
                        or libro_st.get("cover_path")
                    )
                    if not cover_raw and b_id:
                        from utils.library_db import COVERS_DIR

                        for ext in [
                            f"{b_id}_high.jpg",
                            f"{b_id}.jpg",
                            f"{b_id}_cover.jpg",
                            f"{b_id}_original.jpg",
                        ]:
                            cand = os.path.join(COVERS_DIR, ext)
                            if os.path.exists(cand):
                                cover_raw = cand
                                break

                    cover_data = await resolve_cover_data(cover_raw)
                    delivery_files = {}
                    delivery_media = []

                    if cover_data:
                        if isinstance(cover_data, bytes):
                            delivery_files["tomozaki_cover"] = (
                                "cover.jpg",
                                cover_data,
                                "image/jpeg",
                            )
                        elif isinstance(cover_data, str) and os.path.exists(
                            cover_data
                        ):
                            try:
                                with open(cover_data, "rb") as f:
                                    delivery_files["tomozaki_cover"] = (
                                        "cover.jpg",
                                        f.read(),
                                        "image/jpeg",
                                    )
                            except Exception as e:
                                logger.warning(f"Error leyendo portada local: {e}")

                        if "tomozaki_cover" in delivery_files:
                            delivery_media.append(
                                {
                                    "id": "tomozaki_cover",
                                    "media": {
                                        "type": "photo",
                                        "media": "attach://tomozaki_cover",
                                    },
                                }
                            )

                    # 2. Resolver archivo epub
                    epub_bytes = None
                    if isinstance(filepath, str) and os.path.exists(filepath):
                        with open(filepath, "rb") as f:
                            epub_bytes = f.read()
                    elif isinstance(filepath, (bytes, bytearray)):
                        epub_bytes = filepath

                    if epub_bytes:
                        delivery_files["epub_file"] = (
                            filename,
                            io.BytesIO(epub_bytes),
                            "application/epub+zip",
                        )
                        delivery_media.append(
                            {
                                "id": "epub_file",
                                "media": {
                                    "type": "document",
                                    "media": "attach://epub_file",
                                },
                            }
                        )

                    # Construir volume_rows si la serie tiene más de 1 volumen
                    volume_rows = []
                    if len(st.get("libros", {})) > 1:
                        current_row = []
                        for k, bk in st["libros"].items():
                            vol_disp = bk.get("vol_display", bk.get("volume", 0))
                            label = f"🔘 Vol. {vol_disp}" if k == key else f"Vol. {vol_disp}"
                            cb = "noop" if k == key else f"sel_vol|{k}"
                            current_row.append({"text": label, "callback_data": cb})
                            if len(current_row) == 4:
                                volume_rows.append(current_row)
                                current_row = []
                        if current_row:
                            volume_rows.append(current_row)

                    # 3. Construir Bloques Nativos con descarga embebida y botones de navegación
                    rich_blocks_edited = build_book_rich_blocks(
                        libro_st,
                        has_cover=bool("tomozaki_cover" in delivery_files),
                        include_download=True,
                        series_hash_short=series_hash_short,
                        volume_buttons=volume_rows if volume_rows else None,
                        show_nav_buttons=True,
                    )

                    # 4. Editar el Rich Message in-place usando Bloques Nativos
                    res_edit = await RichMessageService.edit_rich_message(
                        chat_id=update.effective_chat.id,
                        message_id=query.message.message_id,
                        blocks=rich_blocks_edited,
                        files=delivery_files if delivery_files else None,
                    )

                    sent_doc = None
                    if res_edit and res_edit.get("ok"):
                        sent_doc = res_edit.get("result")
                        st.setdefault("downloaded_msgs", set()).add(
                            query.message.message_id
                        )
                        st.setdefault("libros_downloaded", {})[
                            query.message.message_id
                        ] = {
                            "libro": libro_st,
                            "series_hash_short": series_hash_short,
                            "files": delivery_files,
                        }
                    else:
                        # Fallback a edición con HTML o envío tradicional
                        html_edited = build_book_rich_html(
                            libro_st,
                            has_cover=bool("tomozaki_cover" in delivery_files),
                            include_download=True,
                            filename=filename,
                        )
                        res_edit_html = await RichMessageService.edit_rich_message(
                            chat_id=update.effective_chat.id,
                            message_id=query.message.message_id,
                            html=html_edited,
                            media=delivery_media if delivery_media else None,
                            files=delivery_files if delivery_files else None,
                            reply_markup=post_keyboard,
                        )
                        if res_edit_html and res_edit_html.get("ok"):
                            sent_doc = res_edit_html.get("result")
                        else:
                            # Fallback tradicional si no se pudo editar
                            vol_val = libro_st.get("volume")
                            vol_str = f" - Volumen {vol_val}" if vol_val else ""
                            chips_generos = format_genre_chips(
                                libro_st.get("tags_json")
                                or libro_st.get("tags")
                                or libro_st.get("generos")
                            )
                        caption_parts = [f"📖 <b>{title}{vol_str}</b>"]
                        if chips_generos:
                            caption_parts.append(f"🏷️ <i>{chips_generos}</i>")
                        if caption:
                            caption_parts.append(f"\n{caption}")
                        sent_doc = await send_doc_bytes(
                            context.bot,
                            update.effective_chat.id,
                            "\n".join(caption_parts),
                            filepath,
                            filename=filename,
                            parse_mode="HTML",
                            reply_markup=post_keyboard,
                            message_thread_id=get_thread_id(update),
                        )

                    # E. Registrar descarga en BD
                    meta_reg = {
                        "book_hash": book_hash,
                        "title": title,
                        "file_size": libro_st.get("file_size"),
                        "autor": libro_st.get("autor"),
                        "id": book_hash,
                        "coverUrl": libro_st.get("portada"),
                    }
                    await register_book_download(
                        bot=context.bot,
                        user_id=uid,
                        meta=meta_reg,
                        sent_doc=sent_doc,
                        download_url=None,
                        title=title,
                    )

                    # Conservar Portada y Sinopsis permanentemente en el chat al descargar con éxito
                    st["last_detalles_msg_ids"] = []

                except Exception as e:
                    logger.error(
                        f"Error enviando o registrando descarga: {e}", exc_info=True
                    )
                    await query.answer(
                        "❌ Error al procesar la descarga. Contacta a un administrador.",
                        show_alert=True,
                    )

            # 12. Publicar en Telegram (Admin / Staff)
            elif data.startswith("info_libro|"):
                key = data.split("|")[1]
                await mostrar_detalles_libro(update, context, key)

            elif data.startswith("pub_menu|"):
                key = data.split("|")[1]
                libro_st = st.get("libros", {}).get(key)
                if not libro_st:
                    await query.answer("⚠️ Información del libro no encontrada.", show_alert=True)
                    return
                title = libro_st.get("titulo", "Novela")
                text = (
                    f"📢 <b>Publicar en Canal de Telegram</b>\n\n"
                    f"📖 <b>Libro:</b> {title}\n\n"
                    f"<i>Selecciona cómo deseas publicar esta novela:</i>"
                )
                try:
                    await query.edit_message_caption(
                        caption=text,
                        reply_markup=BotKeyboards.publish_menu(key),
                        parse_mode="HTML",
                    )
                except Exception:
                    try:
                        await query.edit_message_text(
                            text=text,
                            reply_markup=BotKeyboards.publish_menu(key),
                            parse_mode="HTML",
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=BotKeyboards.publish_menu(key),
                            parse_mode="HTML",
                            message_thread_id=get_thread_id(update),
                        )

            elif data.startswith("pub_sched_menu|"):
                key = data.split("|")[1]
                text = (
                    "⏰ <b>Programar Publicación en Telegram</b>\n\n"
                    "<i>Selecciona cuándo deseas que se publique automáticamente en el canal:</i>"
                )
                try:
                    await query.edit_message_caption(
                        caption=text,
                        reply_markup=BotKeyboards.publish_schedule_presets(key),
                        parse_mode="HTML",
                    )
                except Exception:
                    try:
                        await query.edit_message_text(
                            text=text,
                            reply_markup=BotKeyboards.publish_schedule_presets(key),
                            parse_mode="HTML",
                        )
                    except Exception:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=text,
                            reply_markup=BotKeyboards.publish_schedule_presets(key),
                            parse_mode="HTML",
                            message_thread_id=get_thread_id(update),
                        )

            elif data.startswith("pub_now|"):
                key = data.split("|")[1]
                libro_st = st.get("libros", {}).get(key)
                if not libro_st:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return
                book_hash = libro_st.get("hash")
                await query.answer("🚀 Procesando publicación inmediata...", show_alert=False)

                try:
                    from datetime import datetime, timezone
                    from services.publisher.publisher_service import publisher_service
                    channels_data = await publisher_service.get_channels_with_discovery(active_only=True)
                    tg_channels = [c for c in channels_data.get("telegram", []) if c.get("is_active")]

                    if tg_channels:
                        target_ch_id = tg_channels[0]["id"]
                        await publisher_service.schedule_publication(
                            book_hash=book_hash,
                            channel_id=target_ch_id,
                            scheduled_for=datetime.now(timezone.utc),
                        )
                        await publisher_service.process_queue()
                        success_msg = "✅ <b>¡Publicación enviada con éxito!</b>\n\nSe ha publicado en el canal oficial de Telegram."
                    else:
                        from config.config_settings import config
                        target_id = getattr(config, "TELEGRAM_PUBLISHER_CHANNEL_ID", None) or getattr(config, "CHANNEL_ID", None)
                        if target_id:
                            from repositories.book_repository import BookRepository
                            from services.publisher.telegram_provider import TelegramPublisherProvider
                            from core.db_manager_pg import pg_manager
                            async with pg_manager.get_session() as session:
                                book_repo = BookRepository(session)
                                book_obj = await book_repo.get_by_hash(book_hash)
                                if book_obj:
                                    book_data = publisher_service._build_book_data_dict(book_obj)
                                    provider = TelegramPublisherProvider()
                                    await provider.announce_book(target_id, book_data)
                                    success_msg = f"✅ <b>¡Publicación enviada con éxito!</b>\n\nSe ha publicado en {target_id}."
                                else:
                                    success_msg = "❌ Error: Libro no encontrado en la base de datos."
                        else:
                            success_msg = "⚠️ No hay canales de Telegram configurados para publicar."

                    nav_kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("⬅️ Volver a la Serie", callback_data="volver_ultima"),
                            InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                        ]
                    ])
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=success_msg,
                        parse_mode="HTML",
                        reply_markup=nav_kb,
                        message_thread_id=get_thread_id(update),
                    )
                except Exception as e:
                    logger.error(f"Error publicando en Telegram: {e}", exc_info=True)
                    await query.answer(f"❌ Error al publicar: {e}", show_alert=True)

            elif data.startswith("pub_in|") or data.startswith("pub_preset|"):
                parts = data.split("|")
                key = parts[2]
                libro_st = st.get("libros", {}).get(key)
                if not libro_st:
                    await query.answer("⚠️ Libro no encontrado.", show_alert=True)
                    return
                book_hash = libro_st.get("hash")

                from datetime import datetime, timedelta, timezone
                now = datetime.now(timezone.utc)
                if parts[0] == "pub_in":
                    hours = int(parts[1])
                    sched_time = now + timedelta(hours=hours)
                    time_desc = f"dentro de {hours} hora(s)"
                else:
                    preset = parts[1]
                    tomorrow = now + timedelta(days=1)
                    if preset == "tomorrow_10":
                        sched_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                        time_desc = "mañana a las 10:00 AM (UTC)"
                    else:
                        sched_time = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
                        time_desc = "mañana a las 18:00 PM (UTC)"

                try:
                    from services.publisher.publisher_service import publisher_service
                    channels_data = await publisher_service.get_channels_with_discovery(active_only=True)
                    tg_channels = [c for c in channels_data.get("telegram", []) if c.get("is_active")]

                    if tg_channels:
                        target_ch_id = tg_channels[0]["id"]
                        await publisher_service.schedule_publication(
                            book_hash=book_hash,
                            channel_id=target_ch_id,
                            scheduled_for=sched_time,
                        )
                        sched_msg = f"✅ <b>¡Publicación programada con éxito!</b>\n\n📅 Se publicará automáticamente {time_desc}."
                    else:
                        sched_msg = "⚠️ No hay canales de Telegram activos configurados para programar."

                    nav_kb = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("⬅️ Volver a la Serie", callback_data="volver_ultima"),
                            InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                        ]
                    ])
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=sched_msg,
                        parse_mode="HTML",
                        reply_markup=nav_kb,
                        message_thread_id=get_thread_id(update),
                    )
                except Exception as e:
                    logger.error(f"Error programando publicación: {e}", exc_info=True)
                    await query.answer(f"❌ Error al programar: {e}", show_alert=True)

            # 13. Navigation Go Back
            elif data == "subir_nivel":
                prev_view = st.get("prev_view_local", "main")
                if prev_view == "genres":
                    await mostrar_generos(update, context)
                elif prev_view == "authors":
                    await mostrar_autores_local(
                        update, context, page=st.get("current_page_b", 1)
                    )
                else:
                    await mostrar_menu_principal(update, context)

            elif data == "volver_ultima":
                hist = st.get("historial", [])
                if hist:
                    last_view = hist.pop()
                    st["historial"] = hist
                    view_name = last_view[0]
                    if view_name == "series_list":
                        # Restaurar estado
                        await mostrar_series(
                            update,
                            context,
                            origin_type=last_view[1],
                            filter_val=last_view[2],
                            page=last_view[3],
                        )
                    elif view_name == "volumes_local":
                        # Limpiar mensajes de ficha previos
                        for msg_id in st.get("last_detalles_msg_ids", []):
                            try:
                                await context.bot.delete_message(
                                    chat_id=update.effective_chat.id, message_id=msg_id
                                )
                            except Exception:
                                pass
                        st["last_detalles_msg_ids"] = []
                        await mostrar_volumenes_local(update, context, last_view[1])
                    else:
                        await mostrar_menu_principal(update, context)
                else:
                    await mostrar_menu_principal(update, context)

            # 13. Search Initialization
            elif data == "buscar" or data == "search_init":
                st["esperando_busqueda"] = True
                search_text = (
                    "🔍 <b>Buscador ZeePub v6.0</b>\n\n"
                    "¿Qué novela ligera estás buscando?\n"
                    "<i>Escribe el título, autor o palabra clave a continuación:</i>"
                )
                search_cancel_kb = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⬅️ Volver", callback_data="subir_nivel"),
                        InlineKeyboardButton("🏠 Inicio", callback_data="volver_menu"),
                        InlineKeyboardButton("❌ Salir", callback_data="cerrar"),
                    ]
                ])
                await query.edit_message_text(
                    search_text, reply_markup=search_cancel_kb, parse_mode="HTML"
                )

            # 14. Clean/Delete Interactive Menu
            elif data == "cerrar" or data == "close_menu":
                # Limpiar cualquier mensaje de ficha técnica previo
                for msg_id in st.get("last_detalles_msg_ids", []):
                    try:
                        await context.bot.delete_message(
                            chat_id=update.effective_chat.id, message_id=msg_id
                        )
                    except Exception:
                        pass
                st["last_detalles_msg_ids"] = []

                try:
                    await query.message.delete()
                except Exception:
                    try:
                        await query.edit_message_reply_markup(reply_markup=None)
                    except Exception:
                        pass

            else:
                logger.info(f"Callback no manejado en la v6: {data}")

        except Exception as e:
            logger.error(
                f"Error procesando callback query de la v6: {e}", exc_info=True
            )
            await query.answer(
                "❌ Error en la navegación del catálogo.", show_alert=True
            )
