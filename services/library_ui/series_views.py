# services/library_ui/series_views.py
"""
Vistas de Detalle de Libros y Carrusel de Volúmenes de Serie para Telegram Rich Messages.
"""

import asyncio
import io
import logging
import os
import uuid
from telegram import Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from services.cover_service import resolve_cover_data
from services.keyboard_factory import BotKeyboards
from services.library_service import LibraryService
from services.metadata_orchestrator.metadata_service import metadata_orchestrator
from services.rich_message_service import RichMessageService
from utils.download_limiter import downloads_left
from utils.helpers import (
    get_thread_id,
    get_translator_acronym,
    resolve_title_cascade,
)

from .builders import build_book_rich_blocks, build_book_rich_html
from .lifecycle import is_nav_expired, schedule_message_lifecycle

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

    # 1. Resolver el hash completo de la serie inmediatamente si viene recortado a 16 caracteres
    full_series_hash = await LibraryService.resolve_series_hash(series_hash)
    series_hash = full_series_hash or series_hash

    # 2. Obtener volúmenes de la serie
    volumes = await LibraryService.get_series_volumes(series_hash)
    if not volumes:
        if update.callback_query:
            await update.callback_query.answer(
                "⚠️ No se encontraron volúmenes para esta serie.", show_alert=True
            )
        return

    meta_serie = await LibraryService.get_series_metadata(series_hash)
    user_lang_pref = st.get("title_language", "english")
    from utils.helpers import resolve_series_title
    meta_dict = meta_serie.to_dict() if hasattr(meta_serie, "to_dict") else (meta_serie if isinstance(meta_serie, dict) else {})
    series_name = resolve_series_title(meta_dict, preference=user_lang_pref) if meta_dict else (meta_serie.series_name if meta_serie else "Serie")

    # Ordenar volúmenes numéricamente de menor a mayor
    def parse_vol_num(v):
        vol_raw = v.get("volume")
        try:
            return float(vol_raw) if vol_raw is not None and str(vol_raw).strip() != "" else 0.0
        except (ValueError, TypeError):
            return 999.0

    volumes.sort(key=parse_vol_num)

    is_same_series = bool(
        st.get("current_series_hash")
        and (
            st["current_series_hash"] == series_hash
            or st["current_series_hash"].startswith(series_hash)
            or series_hash.startswith(st["current_series_hash"])
        )
    )

    # Re-poblar estado si cambió de serie o si no hay libros cargados
    need_rebuild = (
        not is_same_series
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
            v_hash = str(v.get("book_hash") or v.get("id") or v.get("hash") or "")
            key = v_hash[:16] if v_hash else uuid.uuid4().hex[:8]
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
            state_manager.register_book_key(key, st["libros"][key])
            if v_hash:
                state_manager.register_book_key(v_hash, st["libros"][key])

            if prev_target_hash and (v_hash == prev_target_hash or key == prev_target_hash or prev_target_hash.startswith(key)):
                matched_key = key

        if matched_key:
            selected_key = matched_key

    st["current_view"] = "volumes_local"
    st["current_series_hash"] = series_hash

    # 2. Paginación y determinación del volumen activo
    all_book_items = list(st["libros"].items())
    total_volumes = len(all_book_items)
    page_size = 8
    total_vol_pages = (total_volumes + page_size - 1) // page_size if total_volumes > 12 else 1

    vol_page = st.get("vol_page", 1)
    if not (1 <= vol_page <= total_vol_pages):
        vol_page = 1

    if selected_key and selected_key in st["libros"]:
        active_key = selected_key
        active_idx = next((i for i, (k, _) in enumerate(all_book_items) if k == active_key), 0)
        vol_page = (active_idx // page_size) + 1 if total_volumes > 12 else 1
    else:
        start_idx = (vol_page - 1) * page_size if total_volumes > 12 else 0
        end_idx = min(start_idx + page_size, total_volumes) if total_volumes > 12 else total_volumes
        page_items = all_book_items[start_idx:end_idx]
        active_key = page_items[0][0]

    st["vol_page"] = vol_page
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

    # 4. Resolver portada del volumen activo con caché de Telegram file_id
    from services.cover_service import get_cached_cover_file_id, set_cached_cover_file_id

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

    cached_fid = (
        get_cached_cover_file_id(str(active_key))
        or (get_cached_cover_file_id(str(book_id)) if book_id else None)
        or (get_cached_cover_file_id(str(cover_raw)) if cover_raw else None)
    )

    files = None
    cover_media = "attach://tomozaki_cover"
    has_cover = False

    if cached_fid:
        cover_media = cached_fid
        has_cover = True
        logger.debug(f"⚡ [mostrar_volumenes_local] Reutilizando file_id de Telegram instantáneo: {cached_fid[:15]}...")
    else:
        cover_data = await resolve_cover_data(cover_raw)
        if cover_data:
            has_cover = True
            if isinstance(cover_data, bytes):
                files = {"tomozaki_cover": ("cover.jpg", cover_data, "image/jpeg")}
            elif isinstance(cover_data, str) and os.path.exists(cover_data):
                try:
                    with open(cover_data, "rb") as f:
                        files = {"tomozaki_cover": ("cover.jpg", f.read(), "image/jpeg")}
                except Exception as e:
                    logger.warning(f"Error al leer archivo de portada local: {e}")

    # 5. Selector de volúmenes (con sub-paginador si la serie supera 12 volúmenes)
    volume_rows = []
    if total_volumes > 1:
        if total_volumes > 12:
            start_idx = (vol_page - 1) * page_size
            end_idx = min(start_idx + page_size, total_volumes)
            display_items = all_book_items[start_idx:end_idx]

            current_row = []
            for k, bk in display_items:
                vol_disp = bk.get("vol_display", bk.get("volume", 0))
                label = f"🔘 Vol. {vol_disp}" if k == active_key else f"Vol. {vol_disp}"
                cb = "noop" if k == active_key else f"sel_vol|{k}"
                current_row.append({"text": label, "callback_data": cb})
                if len(current_row) == 4:
                    volume_rows.append(current_row)
                    current_row = []
            if current_row:
                volume_rows.append(current_row)

            # Fila de control de paginación de volúmenes
            s_short = series_hash[:16] if series_hash else ""
            prev_cb = f"vol_page|{s_short}|{vol_page - 1}" if vol_page > 1 else "noop"
            next_cb = f"vol_page|{s_short}|{vol_page + 1}" if vol_page < total_vol_pages else "noop"
            volume_rows.append([
                {"text": "◀️" if vol_page > 1 else "▫️", "callback_data": prev_cb},
                {"text": f"📚 Volúmenes ({vol_page}/{total_vol_pages})", "callback_data": "noop"},
                {"text": "▶️" if vol_page < total_vol_pages else "▫️", "callback_data": next_cb},
            ])
        else:
            current_row = []
            for k, bk in all_book_items:
                vol_disp = bk.get("vol_display", bk.get("volume", 0))
                label = f"🔘 Vol. {vol_disp}" if k == active_key else f"Vol. {vol_disp}"
                cb = "noop" if k == active_key else f"sel_vol|{k}"
                current_row.append({"text": label, "callback_data": cb})
                if len(current_row) == 4:
                    volume_rows.append(current_row)
                    current_row = []
            if current_row:
                volume_rows.append(current_row)

    is_group = update.effective_chat.type in ("group", "supergroup")

    msg_id = (
        update.callback_query.message.message_id
        if update.callback_query and update.callback_query.message
        else None
    )
    nav_expired = is_nav_expired(chat_id, msg_id)

    # 6. Cuota y rol
    left = await downloads_left(uid)
    can_download = True if left == "ilimitadas" else (isinstance(left, int) and left > 0)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)
    series_hash_short = series_hash[:16] if series_hash else None

    # Si expiró la navegación tras 10 min, no volver a mostrar los botones de navegación
    show_nav_buttons = False if nav_expired else True
    show_admin_buttons = False if nav_expired else is_staff

    # 7. Construir Bloques Nativos (Rich Blocks)
    rich_blocks = build_book_rich_blocks(
        active_book,
        has_cover=has_cover,
        cover_media=cover_media,
        key=active_key,
        can_download=can_download,
        is_admin_or_staff=show_admin_buttons,
        series_hash_short=series_hash_short,
        volume_buttons=volume_rows if volume_rows else None,
        show_nav_buttons=show_nav_buttons,
    )

    # 8. Enviar o editar in-place
    if update.callback_query and not force_new:
        target_mid = update.callback_query.message.message_id
        try:
            res_edit = await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=target_mid,
                blocks=rich_blocks,
                files=files if files else None,
            )
            if res_edit and res_edit.get("ok"):
                # Capturar y cachear file_id devuelto por Telegram
                res_obj = res_edit.get("result", {})
                photos = res_obj.get("photo")
                if photos and isinstance(photos, list) and len(photos) > 0:
                    new_fid = photos[-1].get("file_id")
                    if new_fid:
                        if cover_raw:
                            set_cached_cover_file_id(str(cover_raw), new_fid)
                        if book_id:
                            set_cached_cover_file_id(str(book_id), new_fid)
                        if active_key:
                            set_cached_cover_file_id(str(active_key), new_fid)

                # Programar / Refrescar temporizador de 10 min en cada interacción
                schedule_message_lifecycle(
                    chat_id=chat_id,
                    message_id=target_mid,
                    active_book=active_book,
                    active_key=active_key,
                    volume_rows=volume_rows,
                    files=files,
                    is_group=is_group,
                    bot_inst=context.bot if context else None,
                    series_hash_short=series_hash_short,
                )
                return
        except Exception as e:
            logger.debug(f"[mostrar_volumenes_local] No se pudo editar in-place: {e}")

        if update.callback_query.message:
            try:
                await update.callback_query.message.delete()
            except Exception:
                pass

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=rich_blocks,
        files=files if files else None,
        message_thread_id=thread_id,
    )

    # Programar temporizador de 10 minutos para mensaje nuevo
    if res and res.get("ok"):
        sent_msg_id = res.get("result", {}).get("message_id")
        if sent_msg_id:
            schedule_message_lifecycle(
                chat_id=chat_id,
                message_id=sent_msg_id,
                active_book=active_book,
                active_key=active_key,
                volume_rows=volume_rows,
                files=files,
                is_group=is_group,
                bot_inst=context.bot if context else None,
                series_hash_short=series_hash_short,
            )


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

    book_id = (
        libro_st.get("book_hash")
        or libro_st.get("id")
        or libro_st.get("hash")
        or libro_st.get("descarga")
    )
    meta = await metadata_orchestrator.get_enriched_metadata(book_id)

    st["libros"][key].update(meta)
    libro = st["libros"][key]

    # Si pertenece a una serie, delegar al carrusel unificado de volúmenes
    series_hash = libro.get("series_hash") or meta.get("series_hash") or st.get("current_series_hash")
    if series_hash:
        return await mostrar_volumenes_local(
            update,
            context,
            series_hash=series_hash,
            selected_key=key,
            force_new=False,
        )

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

    left = await downloads_left(uid)
    can_download = (
        True
        if left == "ilimitadas"
        else (isinstance(left, int) and left > 0)
    )
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)
    series_hash = st.get("current_series_hash") or libro.get("series_hash")
    series_hash_short = series_hash[:16] if series_hash else None

    rich_blocks = build_book_rich_blocks(
        libro,
        has_cover=bool(files and "tomozaki_cover" in files),
        key=key,
        can_download=can_download,
        is_admin_or_staff=is_staff,
        series_hash_short=series_hash_short,
    )

    res = await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=rich_blocks,
        files=files if files else None,
        message_thread_id=thread_id,
    )

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
        rich_msg_id = res.get("result", {}).get("message_id")
        if rich_msg_id:
            st["last_detalles_msg_ids"].append(rich_msg_id)
