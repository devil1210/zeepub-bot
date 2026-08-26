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
    mostrar_menu_principal,
    mostrar_generos,
    mostrar_series,
    mostrar_libros,
    mostrar_volumenes_local,
    mostrar_detalles_libro,
    mostrar_autores_local,
)
from services.download_history import register_book_download
from services.cover_service import send_doc_bytes
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

        # 1. Always answer callback to prevent Telegram client from spinning
        try:
            await query.answer()
        except Exception:
            pass

        # Ignore no-op pagination buttons
        if data == "noop":
            return

        try:
            # 1. No-op (Inactive/Disabled Buttons)
            if data == "noop":
                await query.answer()
                return

            # 2. Main Menu Navigation
            elif data == "main_menu" or data == "volver_menu":
                await mostrar_menu_principal(update, context)

            # 3. Categorized Lists Navigation
            elif data.startswith("nav_local|"):
                category = data.split("|")[1]
                if category == "all_series":
                    await mostrar_series(
                        update, context, origin_type="all_series", page=1
                    )
                elif category == "newest":
                    await mostrar_series(update, context, origin_type="newest", page=1)
                elif category == "genres":
                    await mostrar_generos(update, context)
                elif category == "authors":
                    await mostrar_autores_local(update, context, page=1)

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
                    await mostrar_volumenes_local(update, context, series_hash)
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

            # 10. Choose Book (Show Rich Metadata details)
            elif data.startswith("lib|"):
                key = data.split("|")[1]
                # Guardamos historial para volver atrás
                st["historial"] = st.get("historial", [])
                st["historial"].append(("volumes_local", st.get("current_series_hash")))
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

                # B. Mantener el mensaje original intacto (No borrar nada) pero quitarle los botones inline
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=update.effective_chat.id,
                        message_id=query.message.message_id,
                        reply_markup=None,
                    )
                except Exception as e:
                    logger.warning(f"Error removiendo botones del Rich Message: {e}")

                # C. Formatear pie de foto (caption) del archivo (únicamente el slug)
                slug = libro_st.get("slug") or ""
                if slug:
                    caption = slug if slug.startswith("#") else f"#{slug}"
                else:
                    clean_title = re.sub(r"[^\w\s]", "", title).replace(" ", "_")
                    caption = f"#{clean_title}"

                try:
                    # D. Preparar entrega enriquecida con Documento integrado y teclado post-descarga
                    series_hash = st.get("current_series_hash")
                    series_hash_short = series_hash[:16] if series_hash else None
                    post_keyboard = BotKeyboards.post_download(series_hash_short)

                    filename = libro_st.get("filename") or f"{title}.epub"
                    generos = (
                        libro_st.get("tags_json")
                        or libro_st.get("tags")
                        or libro_st.get("generos")
                    )
                    chips_generos = format_genre_chips(generos)

                    vol_val = libro_st.get("volume")
                    vol_str = f" - Volumen {vol_val}" if vol_val else ""
                    html_parts = [
                        f"<h3>📖 {title}{vol_str}</h3>"
                    ]
                    if chips_generos:
                        html_parts.append(f"<p>🏷️ <i>{chips_generos}</i></p>")

                    html_parts.append("<p>✅ <b>¡Tu novela está lista para descargar!</b></p>")
                    html_parts.append(f'<p><a href="tg://document?id=epub_file">📥 {filename}</a></p>')
                    if caption:
                        html_parts.append(f"<p>{caption}</p>")

                    html_delivery = "\n".join(html_parts)

                    # Leer bytes del archivo epub
                    epub_bytes = None
                    if isinstance(filepath, str) and os.path.exists(filepath):
                        with open(filepath, "rb") as f:
                            epub_bytes = f.read()
                    elif isinstance(filepath, (bytes, bytearray)):
                        epub_bytes = filepath

                    rich_sent = False
                    sent_doc = None
                    if epub_bytes:
                        delivery_files = {
                            "epub_file": (
                                filename,
                                io.BytesIO(epub_bytes),
                                "application/epub+zip",
                            )
                        }
                        delivery_media = [
                            {
                                "id": "epub_file",
                                "media": {
                                    "type": "document",
                                    "media": "attach://epub_file",
                                },
                            }
                        ]
                        from services.rich_message_service import RichMessageService

                        res = await RichMessageService.send_rich_message(
                            chat_id=update.effective_chat.id,
                            html=html_delivery,
                            media=delivery_media,
                            files=delivery_files,
                            reply_markup=post_keyboard,
                            message_thread_id=get_thread_id(update),
                        )
                        if res and res.get("ok"):
                            rich_sent = True
                            sent_doc = res.get("result")

                    # Fallback si RichMessage no pudo enviarse
                    if not rich_sent:
                        sent_doc = await send_doc_bytes(
                            context.bot,
                            update.effective_chat.id,
                            caption,
                            filepath,
                            filename=filename,
                            parse_mode="HTML",
                            message_thread_id=get_thread_id(update),
                        )
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=(
                                "✅ <b>¡Novela enviada con éxito!</b>\n\n"
                                "<i>¿Qué quieres hacer ahora? Selecciona una opción del menú:</i>"
                            ),
                            reply_markup=post_keyboard,
                            parse_mode="HTML",
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
