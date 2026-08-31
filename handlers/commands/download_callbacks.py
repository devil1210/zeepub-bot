# handlers/commands/download_callbacks.py
"""
Manejador especializado de descargas directas, paquetes y estrellas para Telegram.
Soporta descargas compartidas en grupos (efímeras y autorizadas) y privadas in-place.
"""

import asyncio
import io
import logging
import os
import re

from telegram import Update
from telegram.ext import ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.cover_service import resolve_cover_data, send_doc_bytes
from services.download_history import register_book_download
from services.keyboard_factory import BotKeyboards
from services.library_ui_service import build_book_rich_blocks, build_book_rich_html
from services.rich_message_service import RichMessageService
from utils.download_limiter import downloads_left
from utils.helpers import format_genre_chips, get_thread_id

logger = logging.getLogger(__name__)


async def handle_download_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> bool:
    """Procesa callbacks relacionados con descarga de libros. Retorna True si fue manejado."""
    query = update.callback_query
    if not query:
        return False

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    # 1. Propinas con Stars
    if data.startswith("stars_tip|"):
        stars_amount = int(data.split("|")[1])
        await query.answer(f"⭐ Procesando aporte de {stars_amount} estrellas...", show_alert=False)
        try:
            from services.payment_service import payment_service

            await payment_service.send_stars_invoice(
                bot=context.bot,
                chat_id=update.effective_chat.id,
                user_id=uid,
                stars=stars_amount,
                title=f"Aporte a la Comunidad ({stars_amount} ⭐)",
                description="Tu apoyo voluntario nos ayuda a mantener y expandir la biblioteca.",
                payload=f"tip_{uid}_{stars_amount}",
            )
        except Exception as e:
            logger.error(f"Error enviando factura de Stars: {e}")
            await query.answer("❌ Error al procesar Stars.", show_alert=True)
        return True

    # 2. Descarga de Libro Individual (Soporta múltiples prefijos de compatibilidad)
    download_prefixes = ("dl_confirm|", "b_dl|", "descargar_epub|", "dl|")
    if any(data.startswith(p) for p in download_prefixes):
        matched_prefix = next(p for p in download_prefixes if data.startswith(p))
        key = data[len(matched_prefix):]

        # A. Buscar libro en el estado del usuario, en el mapa compartido o en cualquier estado activo
        libro_st = state_manager.get_book_by_key(key, uid)

        if not libro_st:
            # Fallback en base de datos por ID o Hash si no está en memoria
            try:
                from core.db_manager_pg import pg_manager
                from repositories.library import BookRepository

                async with pg_manager.get_session() as session:
                    repo = BookRepository(session)
                    b_obj = await repo.get_by_id(key) or await repo.get_by_hash(key)
                    if b_obj:
                        libro_st = {
                            "id": b_obj.id,
                            "book_hash": b_obj.hash_md5,
                            "hash": b_obj.hash_md5,
                            "title": b_obj.title,
                            "titulo": b_obj.title,
                            "filepath": b_obj.filepath,
                            "descarga": b_obj.filepath,
                            "filename": b_obj.filename or f"{b_obj.title}.epub",
                            "file_size": b_obj.file_size,
                            "autor": b_obj.author,
                            "volume": b_obj.volume,
                            "portada": f"/covers/{b_obj.id}.jpg",
                        }
                        state_manager.register_book_key(key, libro_st)
            except Exception as e:
                logger.warning(f"Error buscando libro en BD para key {key}: {e}")

        if not libro_st:
            await query.answer("⚠️ Libro no encontrado o sesión expirada.", show_alert=True)
            return True

        # B. Chequeo de Límites de Descarga
        left = await downloads_left(uid)
        is_admin_user = uid in getattr(config, "ADMIN_USERS", []) or uid == 133994080
        if not is_admin_user and left != "ilimitadas" and isinstance(left, int) and left <= 0:
            await query.answer(
                "🚫 Has alcanzado tu límite diario de descargas. Vuelve mañana o adquiere un rango con /donar.",
                show_alert=True,
            )
            return True

        # C. Feedback visual inmediato
        await query.answer("🚀 Procesando archivo EPUB...", show_alert=False)

        # D. Metadatos y ruta
        filepath = libro_st.get("filepath") or libro_st.get("descarga")
        title = libro_st.get("title") or libro_st.get("titulo", "Libro")
        book_hash = (
            libro_st.get("hash")
            or libro_st.get("book_hash")
            or libro_st.get("id")
            or f"{title}_{libro_st.get('volume', 1)}"
        )

        caption = ""
        series_name = (
            libro_st.get("series_name")
            or libro_st.get("series")
            or st.get("current_series_title")
        )
        if series_name:
            clean_tag = re.sub(r"[^\w\s]", "", series_name).replace(" ", "_")
            caption = f"#{clean_tag}"
        elif title:
            clean_title = re.sub(r"[^\w\s]", "", title).replace(" ", "_")
            caption = f"#{clean_title}"

        try:
            filename = libro_st.get("filename") or f"{title}.epub"
            series_hash = st.get("current_series_hash") or libro_st.get("series_hash")
            series_hash_short = series_hash[:16] if series_hash else None
            post_keyboard = BotKeyboards.post_download(series_hash_short)

            # 1. Resolver portada
            b_id = (
                libro_st.get("book_hash")
                or libro_st.get("id")
                or libro_st.get("hash")
                or series_hash
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
                elif isinstance(cover_data, str) and os.path.exists(cover_data):
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

            from services.telegram_service import is_authorized_group, enviar_libro_directo

            is_group = update.effective_chat.type in ("group", "supergroup")
            is_authorized = is_authorized_group(update.effective_chat.id)
            thread_id = get_thread_id(update)

            sent_doc = None

            # Si es un grupo (autorizado o no), enviamos el documento como mensaje nuevo para no romper la ficha interactiva compartida
            if is_group:
                if not is_authorized:
                    from services.settings_service import get_setting

                    try:
                        del_mins = int(get_setting("auto_delete_time", "2") or "2")
                        auto_delete_sec = max(60, del_mins * 60)
                    except Exception:
                        auto_delete_sec = 120

                    sent_doc = await enviar_libro_directo(
                        bot=context.bot,
                        user_id=uid,
                        title=title,
                        download_url=filepath,
                        target_chat_id=update.effective_chat.id,
                        message_thread_id=thread_id,
                        metadata_override=libro_st,
                        explicit_file_buffer=epub_bytes,
                        auto_delete_seconds=auto_delete_sec,
                        job_queue=getattr(context, "job_queue", None),
                    )
                else:
                    sent_doc = await enviar_libro_directo(
                        bot=context.bot,
                        user_id=uid,
                        title=title,
                        download_url=filepath,
                        target_chat_id=update.effective_chat.id,
                        message_thread_id=thread_id,
                        metadata_override=libro_st,
                        explicit_file_buffer=epub_bytes,
                        auto_delete_seconds=0,
                        job_queue=getattr(context, "job_queue", None),
                    )
            else:
                # Chat Privado: Edición in-place del Rich Message
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

                rich_blocks_edited = build_book_rich_blocks(
                    libro_st,
                    has_cover=bool("tomozaki_cover" in delivery_files),
                    include_download=True,
                    series_hash_short=series_hash_short,
                    volume_buttons=volume_rows if volume_rows else None,
                    show_nav_buttons=True,
                )

                res_edit = await RichMessageService.edit_rich_message(
                    chat_id=update.effective_chat.id,
                    message_id=query.message.message_id,
                    blocks=rich_blocks_edited,
                    files=delivery_files if delivery_files else None,
                )

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
                            message_thread_id=thread_id,
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

            st["last_detalles_msg_ids"] = []

        except Exception as e:
            logger.error(f"Error enviando o registrando descarga: {e}", exc_info=True)
            await query.answer(
                "❌ Error al procesar la descarga. Contacta a un administrador.",
                show_alert=True,
            )
        return True

    return False
