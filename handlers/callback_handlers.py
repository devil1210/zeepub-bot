# handlers/callback_handlers.py

import logging
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from config.config_settings import config
from core.state_manager import state_manager
from services.library_service import LibraryService
from services.library_ui_service import (
    mostrar_autores_local,
    mostrar_generos,
    mostrar_menu_principal,
    mostrar_resultados_locales,
    mostrar_series,
    mostrar_volumenes_local,
)

logger = logging.getLogger(__name__)


async def set_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    uid = update.effective_user.id
    _, destino = query.data.split("|", 1)
    st = state_manager.get_user_state(uid)

    # Destinos preconfigurados o "aqui"
    if destino == "aqui" or destino in ("@ZeePubBotTest", "@ZeePubs"):
        st["destino"] = update.effective_chat.id if destino == "aqui" else destino
        st["titulo"] = "📚 Categorías"
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_text = "✅ Destino seleccionado"
        text = base_text
        if cms and cms.enabled:
            text = await cms.get_text("destination_selected")
        await query.answer(text)

        # Ir directamente a la Biblioteca Local (basada en BD local)
        # (mostrar_menu_principal is imported globally)

        await mostrar_menu_principal(update, context)
        return

    # Destino manual
    if destino == "otro":
        st["esperando_destino_manual"] = True
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_manual = "✏️ Escribe @usuario o chat_id para publicar:"
        text_manual = await cms.get_text("manual_destination_prompt") if (cms and cms.enabled) else base_manual
        await query.edit_message_text(text_manual)
        return


async def ver_catalogo_normal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Acceso directo al catálogo normal para administradores."""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    st["titulo"] = "📚 Biblioteca Local"
    # await mostrar_menu_principal(update, context) (Global import)

    await mostrar_menu_principal(update, context)


async def handle_manual_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura texto tras elegir 'Otro' para destino manual."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    if not st.get("esperando_destino_manual"):
        return

    destino_text = update.message.text.strip()
    st["destino"] = destino_text
    st.pop("esperando_destino_manual", None)
    st["titulo"] = "📚 Categorías"

    # Redirigir siempre a menú principal local
    # Redirigir siempre a menú principal local
    # from services.library_ui_service import mostrar_menu_principal

    await mostrar_menu_principal(update, context)


async def handle_search_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura texto tras /search o tras inline 'Buscar EPUB'."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    if not st.get("esperando_busqueda"):
        return

    termino = update.message.text.strip()
    st.pop("esperando_busqueda", None)

    # 1. Búsqueda de Series (Agrupada)
    res_series = await LibraryService.search_series(termino, items_per_page=30)
    series_list = res_series.get("items", [])
    series_hashes = {s["series_hash"] for s in series_list}

    # 2. Búsqueda de Libros Individuales
    res_books = await LibraryService.search_books(termino)
    all_books = res_books.get("results", [])

    # Filtramos libros que YA pertenecen a las series encontradas
    books_standalone = [b for b in all_books if b.get("series_hash") not in series_hashes]

    await mostrar_resultados_locales(update, context, termino, series_list, books_standalone)


async def abrir_zeepubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await mostrar_menu_principal(update, context)


async def buscar_epub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el botón 'Buscar EPUB': pide texto al usuario."""
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    chat = update.effective_chat

    st["esperando_busqueda"] = True
    st["current_view"] = "search"

    if chat.type == "private":
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_search = "🔍 ¿Qué libro buscas? Escribe el título o autor:"
        text_search = await cms.get_text("search_prompt") if (cms and cms.enabled) else base_search
        await query.edit_message_text(text_search)
        return

    # En grupos, verificar si el bot es administrador
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        is_admin = bot_member.status in ["administrator", "creator"]
    except Exception:
        is_admin = False

    if is_admin:
        # Bot es admin: puede recibir mensajes normales
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_search = "🔍 ¿Qué libro buscas? Escribe el título o autor:"
        text_search = await cms.get_text("search_prompt") if (cms and cms.enabled) else base_search
        await query.edit_message_text(text_search)
    else:
        # Bot NO es admin: solo recibe comandos
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_instr = (
            "🔍 Para buscar, usa el comando:\n\n"
            "<code>/search término de búsqueda</code>\n\n"
            "Ejemplo: <code>/search harry potter</code>"
        )
        text_instr = base_instr
        if cms and cms.enabled:
            text_instr = await cms.get_text("search_instructions_legacy")

        await query.edit_message_text(
            text_instr,
            parse_mode="HTML",
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    data = query.data
    uid = update.effective_user.id

    # Skip callbacks handled by plugins
    plugin_prefixes = ("setlog|", "help|", "close")
    if data and any(data.startswith(prefix) for prefix in plugin_prefixes):
        return

    st = state_manager.get_user_state(uid)

    # Check ban status
    from services.user_service import get_effective_user

    user_info = await get_effective_user(uid)
    if user_info.get("role") == "banned":
        expires_at = user_info.get("expires_at")
        msg = "⛔ Estás <b>baneado</b> del bot."
        if expires_at:
            msg += f" Hasta: <b>{expires_at.strftime('%Y-%m-%d %H:%M')}</b>"
        await query.answer(msg.replace("<b>", "").replace("</b>", ""), show_alert=True)
        await query.answer(msg.replace("<b>", "").replace("</b>", ""), show_alert=True)
        return

    # Recomendaciones (v6.1.0)

    if data == "rec|ver":
        # Deshabilitado temporalmente hasta tener implementacion local
        await query.answer("⚠️ Función en mantenimiento.", show_alert=True)
        return

    # Ver Catálogo Normal (Local)
    if data == "ver_catalogo_normal":
        await mostrar_menu_principal(update, context)
        return

    # === Local Navigation Dispatchers ===
    if data == "nav_local|genres":
        await mostrar_generos(update, context)
        return
    if data == "nav_local|authors":
        await mostrar_autores_local(update, context)
        return
    if data == "nav_local|recent_books":
        from services.library_ui_service import mostrar_libros

        await mostrar_libros(update, context, origin_type="recent")
        return
    if data.startswith("nav_local|"):
        _, origin = data.split("|", 1)
        await mostrar_series(update, context, origin_type=origin)
        return
    if data.startswith("gen|"):
        _, tag = data.split("|", 1)
        await mostrar_series(update, context, origin_type="genre", filter_val=tag)
        return
    if data.startswith("aut|"):
        _, auth = data.split("|", 1)
        await mostrar_series(update, context, origin_type="author", filter_val=auth)
        return
    if data.startswith("nav_b|"):
        from services.library_ui_service import mostrar_libros

        parts = data.split("|")
        # Format: nav_b|origin|filter|page
        origin = parts[1]
        filter_v = parts[2]
        page = int(parts[3])
        await mostrar_libros(update, context, origin_type=origin, filter_val=filter_v or None, page=page)
        return
    if data.startswith("nav_p|"):
        parts = data.split("|")
        # Format: nav_p|origin|filter|page
        origin = parts[1]
        filter_v = parts[2]
        page = int(parts[3])
        await mostrar_series(update, context, origin_type=origin, filter_val=filter_v or None, page=page)
        return

    if data.startswith("nav_au|"):
        parts = data.split("|")
        page = int(parts[1])
        await mostrar_autores_local(update, context, page=page)
        return

    # Selección de colección (Series Local)
    if data.startswith("col|"):
        idx = int(data.split("|", 1)[1])
        col = st["colecciones"].get(idx)
        if col:
            href = col.get("href", "")
            if href.startswith("local_series|"):
                series_hash = href.split("|")[1]
                await mostrar_volumenes_local(update, context, series_hash)
                return
            else:
                # Si no es local, ignorar o mostrar error, ya que OPDS está deshabilitado
                await query.answer("⚠️ Recurso no disponible localmente.", show_alert=True)
        return

    # Selección de libro
    if data.startswith("lib|"):
        # Limpiar estado temporal de libro anterior
        for k in (
            "epub_buffer",
            "meta_pendiente",
            "portada_pendiente",
            "titulo_pendiente",
            "fb_caption",
        ):
            st.pop(k, None)
        key = data.split("|", 1)[1]
        libro = None
        if key.startswith("local_"):
            # Stateless lookup from DB (for recommendations/scheduler)
            try:
                local_id = int(key.split("_")[1])
                from repositories.book_repository import book_repo

                book_db = await book_repo.get_by_id(local_id)
                if book_db:
                    # Construct pseudo 'libro' dict
                    libro = {
                        "titulo": book_db.title,
                        "portada": book_db.cover_low or book_db.cover_medium or book_db.cover_high,
                        "descarga": book_db.filepath,
                        "href": book_db.filepath,
                    }
            except Exception as e:
                logger.error(f"Error fetching local book {key}: {e}")

        # Fallback to session state if not found via stateless or not local key
        if not libro:
            libro = st["libros"].get(key)

        if not libro:
            # Try refreshing if session expired? Or just fail gracefully
            try:
                await query.answer("⚠️ Sesión expirada o libro no encontrado.", show_alert=True)
            except Exception:
                pass
            return

        href = libro.get("descarga") or libro.get("href")
        m = re.search(r"/series/(\d+)/volume/(\d+)/", href)
        if m:
            st["series_id"], st["volume_id"] = m.group(1), m.group(2)
        st["ultima_pagina"] = st.get("url")

        # Preparar menú y mensaje "Preparando..."
        actual_destino = st.get("destino") or update.effective_chat.id
        chat_origen = st.get("chat_origen") or update.effective_chat.id
        menu_prep = None
        if actual_destino == chat_origen:
            try:
                await context.bot.delete_message(chat_id=chat_origen, message_id=query.message.message_id)
            except Exception:
                logger.debug("No se pudo borrar menú")
            try:
                thread_id = st.get("message_thread_id")  # Usar el guardado
                prep = await context.bot.send_message(
                    chat_id=chat_origen,
                    text="⏳ Preparando...",
                    message_thread_id=thread_id,
                )
                menu_prep = (chat_origen, prep.message_id)
            except Exception as e:
                logger.debug("No se pudo enviar 'Preparando...': %s", e)

        # If user is a publisher/admin, honor their ephemeral publish target if set
        if uid in config.FACEBOOK_PUBLISHERS or uid in config.ADMIN_USERS:
            default_target = st.pop("publish_target_temp", None)
            if default_target == "facebook":
                st["pending_pub_book"] = {
                    "titulo": libro.get("titulo", ""),
                    "portada": libro.get("portada", ""),
                    "href": href,
                }
                st["pending_pub_menu_prep"] = menu_prep
                st["publish_command_origin"] = update.effective_chat.id
                st["publish_command_thread_id"] = st.get("message_thread_id")
                from services.facebook_service import _publish_choice_facebook

                await _publish_choice_facebook(update, context, uid)
                return
            elif default_target == "telegram":
                from services.telegram_service import publicar_libro

                await publicar_libro(
                    update,
                    context,
                    uid,
                    libro["titulo"],
                    libro.get("portada", ""),
                    href,
                    menu_prep=menu_prep,
                )
                if actual_destino != chat_origen:
                    try:
                        cms = context.application.plugin_manager.get_plugin("custom_messages")
                        base_success = f"✅ Publicado: {libro['titulo']}"
                        text_success = (
                            await cms.get_text("publish_success_telegram", Titulo=libro["titulo"])
                            if (cms and cms.enabled)
                            else base_success
                        )
                        await query.edit_message_text(text_success)
                    except Exception:
                        logger.debug("Error al editar confirmación")
                return
            # If no temp target is set, fall through to normal behavior (no menu)

        # Publicar EPUB (non-publishers or publisher with no temp)
        from services.telegram_service import publicar_libro

        await publicar_libro(
            update,
            context,
            uid,
            libro["titulo"],
            libro.get("portada", ""),
            href,
            menu_prep=menu_prep,
        )
        if actual_destino != chat_origen:
            try:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_success = f"✅ Publicado: {libro['titulo']}"
                text_success = (
                    await cms.get_text("publish_success_telegram", Titulo=libro["titulo"])
                    if (cms and cms.enabled)
                    else base_success
                )
                await query.edit_message_text(text_success)
            except Exception:
                logger.debug("Error al editar confirmación")
        return

    # Publisher flow: publish target selection
    if data.startswith("publish_target|"):
        choice = data.split("|", 1)[1]
        uid = update.effective_user.id
        st = state_manager.get_user_state(uid)
        logger.debug(
            "publish_target callback for uid=%s choice=%s pending=%s origin=%s",
            uid,
            choice,
            st.get("pending_pub_book"),
            st.get("publish_command_origin"),
        )
        if choice == "facebook":
            from services.facebook_service import _publish_choice_facebook

            await _publish_choice_facebook(update, context, uid)
        elif choice == "telegram":
            # Continue publishing using stored pending data
            pending = st.get("pending_pub_book")
            if not pending:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_text = "No hay publicación pendiente."
                text = base_text
                if cms and cms.enabled:
                    text = await cms.get_text("no_pending_publication")
                await query.answer(text)
            else:
                # use the module-level publicar_libro imported at top
                # Clear pending flag then call publicar_libro to proceed
                menu_prep = st.pop("pending_pub_menu_prep", None)
                st.pop("pending_pub_book", None)
                # Clear pending flag then call publicar_libro to proceed
                from services.telegram_service import publicar_libro

                await publicar_libro(
                    update,
                    context,
                    uid,
                    pending.get("titulo"),
                    pending.get("portada"),
                    pending.get("href"),
                    menu_prep=menu_prep,
                )
        else:
            # Cancel / Exit
            st.pop("pending_pub_book", None)
            st.pop("pending_pub_menu_prep", None)
            st.pop("publish_command_origin", None)
            st.pop("publish_command_thread_id", None)
            try:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_cancel = "⛔ Publicación cancelada."
                text_cancel = await cms.get_text("publish_cancelled") if (cms and cms.enabled) else base_cancel
                await query.edit_message_text(text_cancel)
            except Exception:
                pass
        try:
            await query.answer()
        except Exception as e:
            logger.debug("Could not answer publish_target callback: %s", e)
        return

    # Set ephemeral publish selection at /start (applies to next book only)
    if data.startswith("set_publish_temp|"):
        _, choice = data.split("|", 1)
        if choice not in ("telegram", "facebook", "none"):
            try:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_text = "Opción inválida"
                text = base_text
                if cms and cms.enabled:
                    text = await cms.get_text("invalid_option")
                await query.answer(text)
            except Exception:
                pass
            return
        if choice == "none":
            st.pop("publish_target_temp", None)
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_cleared = "⚪ Preferencia temporal de publicación descartada."
            text = await cms.get_text("publish_preference_cleared") if (cms and cms.enabled) else base_cleared
        else:
            # Set one-time publish target that will be popped at next selection
            st["publish_target_temp"] = choice
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_set = f"✅ Publicación temporal establecida para el próximo libro: {choice}."
            text = await cms.get_text("publish_preference_set", Destino=choice) if (cms and cms.enabled) else base_set

        # For non-admin publishers, proceed to show the normal collections
        # menu now (but don't ask for Evil destination). If the user picked
        # Facebook, assume publishing in this chat as destination.

        # SIEMPRE redigir a menú local ya que OPDS está deshabilitado
        st["historial"] = []
        if choice == "facebook":
            st["destino"] = update.effective_chat.id
            st["chat_origen"] = update.effective_chat.id

        await mostrar_menu_principal(update, context)
        return

    # Subir nivel
    if data == "subir_nivel":
        view = st.get("current_view")
        if view == "series_list":
            prev_view = st.get("prev_view_local")
            if prev_view == "genres":
                await mostrar_generos(update, context)
                return
            elif prev_view == "authors":
                await mostrar_autores_local(update, context)
                return
            else:
                await mostrar_menu_principal(update, context)
                return
        if view in ("genres", "authors", "all_series", "newest", "search_results", "volumes_local"):
            await mostrar_menu_principal(update, context)
            return

        # Default back to main
        await mostrar_menu_principal(update, context)
        return

    # Volver a categorías raíz
    if data == "volver_colecciones":
        await mostrar_menu_principal(update, context)
        return

    # Volver a última página donde se listaban los EPUB
    if data == "volver_ultima":
        # Borrar mensaje de botones (el actual)
        try:
            await query.message.delete()
        except Exception:
            pass

        # Si estábamos en volumes_local o search_results

        # Por simplicidad, volvemos al menú principal o tratamos de recrear la vista.
        # Dado que no guardamos el objeto "search_results" en estado completo,
        # lo más seguro es volver al menú principal en modo local estricto
        # O volver a la serie si tenemos hash

        current_series_hash = st.get("current_series_hash")
        if current_series_hash:
            await mostrar_volumenes_local(update, context, current_series_hash)
        else:
            await mostrar_menu_principal(update, context)
        return

    # Cerrar menú
    if data == "cerrar":
        cms = context.application.plugin_manager.get_plugin("custom_messages")

        base_closing = "👋 Gracias por usar el bot."
        text_closing = base_closing
        if cms and cms.enabled:
            text_closing = await cms.get_text("bot_closing")

        await query.edit_message_text(text_closing)
        return

    # Descargar EPUB pendiente
    if data == "descargar_epub":
        try:
            await query.answer()
        except Exception as e:
            logger.debug("Could not answer callback for descargar_epub: %s", e)
        from services.telegram_service import descargar_epub_pendiente

        await descargar_epub_pendiente(update, context, uid, job_queue=context.job_queue)
        return

    # Rating Handler
    if data.startswith("rate_book|"):
        # Format: rate_book|book_id|rating (or 'cancel')
        parts = data.split("|")
        if len(parts) >= 3:
            try:
                book_id_str = parts[1]
                # Check for cancel
                if parts[2] == "cancel":
                    try:
                        await query.delete_message()
                    except Exception:
                        pass
                    return

                rating_val = int(parts[2])
                import services.rating_service as rs

                # Strip prefix "local_" if present, though IDs should be int usually
                # but local_books use int IDs.
                # If ID comes as "local_123", strip "local_"
                clean_id = int(book_id_str.replace("local_", ""))

                await rs.RatingService.rate_book(uid, clean_id, rating_val)

                # Feedback to user
                await query.answer(f"⭐ ¡Gracias! Votaste {rating_val}/5.", show_alert=False)

                # Update message to show current status (remove keyboard or show static stars)
                # We can replace keyboard with a "Thanks" button or remove it
                msg_text = query.message.text_html
                # Append user rating info if not present
                if "Tu voto:" not in msg_text:
                    msg_text += f"\n\n✅ <b>Tu voto:</b> {rating_val} ⭐"

                try:
                    await query.edit_message_text(msg_text, parse_mode="HTML", reply_markup=None)
                except Exception:
                    pass

            except ValueError:
                await query.answer("❌ Error al procesar voto.")
        return

    # Trigger Rating Prompt (e.g. from "Calificar" button)
    if data.startswith("prompt_rate|"):
        book_id = data.split("|")[1]

        # Build 1-5 Scale Keyboard
        keyboard = [
            [
                InlineKeyboardButton("1 ⭐", callback_data=f"rate_book|{book_id}|1"),
                InlineKeyboardButton("2 ⭐", callback_data=f"rate_book|{book_id}|2"),
                InlineKeyboardButton("3 ⭐", callback_data=f"rate_book|{book_id}|3"),
                InlineKeyboardButton("4 ⭐", callback_data=f"rate_book|{book_id}|4"),
                InlineKeyboardButton("5 ⭐", callback_data=f"rate_book|{book_id}|5"),
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data=f"rate_book|{book_id}|cancel")],
        ]

        await query.message.reply_text(
            "⭐ <b>Califica este libro:</b>\n¿Qué te pareció?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )
        await query.answer()
        return

    # Facebook handlers
    if data == "preparar_post_fb":
        from services.facebook_service import preparar_post_facebook

        await preparar_post_facebook(update, context, uid)
        try:
            await query.answer()
        except Exception as e:
            logger.debug("Could not answer callback for preparar_post_fb: %s", e)
        return

    if data == "publicar_fb":
        from services.facebook_service import publicar_facebook_action

        await publicar_facebook_action(update, context, uid)
        try:
            await query.answer()
        except Exception as e:
            logger.debug("Could not answer callback for publicar_fb: %s", e)
        return

    if data == "descartar_fb":
        try:
            # Keep the message content but remove inline buttons (reply_markup)
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                # Fallback for older versions or partial support
                try:
                    await query.edit_message_text(text=query.message.text)
                except Exception:
                    pass
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_text = "🗑️ Descartado"
            text = base_text
            if cms and cms.enabled:
                text = await cms.get_text("fb_preview_discarded")
            await query.answer(text)
        except Exception as e:
            logger.debug("Could not discard FB preview buttons: %s", e)
        return

    # Handler: Cancelar Donación
    if data.startswith("cancelar_donacion|"):
        await cancelar_donacion(update, context)
        return

    # Handler: Notificar Donación (con protección de usuario)
    if data.startswith("notificar_donacion") or data == "notificar_donacion":
        try:
            # Compatibilidad con formato antiguo sin UID (si existe alguno)
            target_uid = None
            if "|" in data:
                try:
                    target_uid = int(data.split("|")[1])
                except (ValueError, IndexError):
                    pass

            # Verificar usuario si hay target_uid
            clicker_uid = update.effective_user.id
            if target_uid and clicker_uid != target_uid:
                try:
                    cms = context.application.plugin_manager.get_plugin("custom_messages")
                    base_text = "⚠️ Este botón no es para ti."
                    text = base_text
                    if cms and cms.enabled:
                        text = await cms.get_text("button_unauthorized")
                    await query.answer(text, show_alert=True)
                except Exception:
                    pass
                return

            # 1. Establecer estado esperando comprobante (globalmente para que funcione al ir al privado)
            # Usamos target_uid si existe, o el clicker si no (para fallback)
            user_to_update = target_uid if target_uid else clicker_uid
            st = state_manager.get_user_state(user_to_update)
            st["waiting_for_donation_proof"] = True

            cms = context.application.plugin_manager.get_plugin("custom_messages")

            # Intentar borrar el mensaje original
            try:
                await query.message.delete()
            except Exception:
                pass

            # 2. Verificar si es chat privado
            if update.effective_chat.type != "private":
                try:
                    bot_username = context.bot.username
                    if not bot_username:
                        try:
                            me = await context.bot.get_me()
                            bot_username = me.username
                        except Exception as e:
                            logger.warning(f"Could not get bot username for URL button: {e}")

                    # URL simple sin parámetros (no muestra /start en el chat)
                    url_button = f"https://t.me/{bot_username}" if bot_username else "https://t.me/ZeePubBot"

                    keyboard = [[InlineKeyboardButton("📩 Enviar comprobante aquí", url=url_button)]]

                    # Obtener mensaje desde template
                    base_redirect = f"👋 Hola {update.effective_user.mention_html()},\n\nPara proteger tu privacidad, por favor envíame el comprobante a mi chat privado pulsando el botón de abajo."
                    text_redirect = base_redirect
                    if cms and cms.enabled:
                        text_redirect = await cms.get_text("donation_redirect_prompt", user=update.effective_user)

                    base_text = "✅ Solicitud registrada."
                    text_answer = base_text
                    if cms and cms.enabled:
                        text_answer = await cms.get_text("donation_request_registered")
                    await query.answer(text_answer)
                    prompt_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text_redirect,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="HTML",
                        message_thread_id=update.effective_message.message_thread_id
                        if update.effective_message.is_topic_message
                        else None,
                    )

                    # Enviar instrucciones proactivamente al chat privado
                    timeout_min = 10
                    # Botones: Cancelar
                    keyboard_cancel = [
                        [
                            InlineKeyboardButton(
                                "❌ Cancelar Registro",
                                callback_data=f"cancelar_donacion|{user_to_update}",
                            )
                        ]
                    ]

                    base_request = (
                        "🧾 <b>Comprobante Requerido</b>\n\n"
                        "Por favor, envía una <b>captura de pantalla</b> o <b>archivo PDF</b> de tu comprobante de donación.\n"
                        "Lo revisaremos para actualizar tu nivel.\n\n"
                        f"⏳ Tienes <b>{timeout_min} minutos</b> para enviar el comprobante."
                    )
                    text_request = base_request
                    if cms and cms.enabled:
                        text_request = await cms.get_text(
                            "donation_proof_request",
                            user=update.effective_user,
                            Tiempo=timeout_min,
                        )

                    try:
                        prompt_private = await context.bot.send_message(
                            chat_id=user_to_update,
                            text=text_request,
                            reply_markup=InlineKeyboardMarkup(keyboard_cancel),
                            parse_mode="HTML",
                        )

                        # Programar timeout para el mensaje privado proactivo
                        if context.job_queue:
                            job_name_p = f"donation_timeout_{user_to_update}_{prompt_private.message_id}"
                            st["donation_timeout_job_name"] = job_name_p
                            context.job_queue.run_once(
                                donation_timeout_job,
                                timeout_min * 60,
                                data={
                                    "uid": user_to_update,
                                    "msg_id": prompt_private.message_id,
                                    "user": update.effective_user,
                                },
                                name=job_name_p,
                            )
                    except Exception as e:
                        logger.warning(f"No se pudo enviar mensaje al privado: {e}")

                    # Programar auto-borrado del prompt del grupo en 2 minutos (120s)
                    if context.job_queue:
                        context.job_queue.run_once(
                            delete_message_job,
                            120,
                            data={
                                "chat_id": update.effective_chat.id,
                                "message_id": prompt_msg.message_id,
                            },
                            name=f"del_donation_prompt_{prompt_msg.message_id}",
                        )

                except Exception as e:
                    logger.error(f"Error answering query in group: {e}")
                return

            # 3. Es chat privado
            # Timeout de 10 minutos (definido por el usuario)
            timeout_min = 10

            # Botones: Cancelar
            keyboard = [
                [
                    InlineKeyboardButton(
                        "❌ Cancelar Registro",
                        callback_data=f"cancelar_donacion|{user_to_update}",
                    )
                ]
            ]

            base_request = (
                "🧾 <b>Comprobante Requerido</b>\n\n"
                "Por favor, envía una <b>captura de pantalla</b> o <b>archivo PDF</b> de tu comprobante de donación.\n"
                "Lo revisaremos para actualizar tu nivel.\n\n"
                f"⏳ Tienes <b>{timeout_min} minutos</b> para enviar el comprobante."
            )
            text_request = base_request
            if cms and cms.enabled:
                text_request = await cms.get_text(
                    "donation_proof_request",
                    user=update.effective_user,
                    Tiempo=timeout_min,
                )

            await query.answer()
            prompt_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_request,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )

            # Programar timeout
            if context.job_queue:
                job_name = f"donation_timeout_{user_to_update}_{prompt_msg.message_id}"
                st["donation_timeout_job_name"] = job_name
                context.job_queue.run_once(
                    donation_timeout_job,
                    timeout_min * 60,
                    data={
                        "uid": user_to_update,
                        "msg_id": prompt_msg.message_id,
                        "user": update.effective_user,
                    },
                    name=job_name,
                )

        except Exception as e:
            logger.error(f"Error handling notificar_donacion: {e}", exc_info=True)
            try:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_text = "❌ Ocurrió un error al procesar tu solicitud."
                text = base_text
                if cms and cms.enabled:
                    text = await cms.get_text("request_processing_error")
                await query.answer(text, show_alert=True)
            except Exception:
                pass
        return

    # Handler: Cerrar Donación (con protección de usuario)
    if data.startswith("cerrar_donacion|"):
        try:
            target_uid = int(data.split("|")[1])
            clicker_uid = update.effective_user.id
            if clicker_uid != target_uid:
                cms = context.application.plugin_manager.get_plugin("custom_messages")
                base_text = "⚠️ Este botón no es para ti."
                text = base_text
                if cms and cms.enabled:
                    text = await cms.get_text("button_unauthorized")
                await query.answer(text, show_alert=True)
                return
            await query.message.delete()
        except Exception:
            pass
        return

    # Nuevo Handler: Ir Privado
    if data.startswith("ir_privado|"):
        try:
            target_uid = int(data.split("|")[1])
            clicker_uid = update.effective_user.id

            if clicker_uid != target_uid:
                try:
                    cms = context.application.plugin_manager.get_plugin("custom_messages")
                    base_text = "⚠️ Este botón no es para ti."
                    text = base_text
                    if cms and cms.enabled:
                        text = await cms.get_text("button_unauthorized")
                    await query.answer(text, show_alert=True)
                except Exception:
                    pass
                return

            # Es el usuario correcto
            try:
                await query.message.delete()
            except Exception:
                pass

            # Redirigir al privado Y enviar instrucciones
            bot_username = context.bot.username
            if not bot_username:
                try:
                    me = await context.bot.get_me()
                    bot_username = me.username
                except Exception as e:
                    logger.warning(f"Could not get bot username for redirect: {e}")

            cms = context.application.plugin_manager.get_plugin("custom_messages")

            # Obtener texto de instrucciones
            base_request = (
                "🧾 <b>Comprobante Requerido</b>\n\n"
                "Por favor, envía una <b>captura de pantalla</b> o <b>archivo PDF</b> de tu comprobante de donación aquí.\n"
                "Lo revisaremos para actualizar tu nivel."
            )
            text_request = base_request
            if cms and cms.enabled:
                text_request = await cms.get_text("donation_proof_request", user=update.effective_user)

            try:
                await context.bot.send_message(chat_id=target_uid, text=text_request, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"No se pudo enviar mensaje al privado (usuario no ha iniciado bot?): {e}")

            if bot_username:
                # Sanitizar username
                bot_username = bot_username.replace("@", "")
                # Usar protocolo nativo para asegurar que abra la app
                redirect_url = f"tg://resolve?domain={bot_username}&start=donation_proof"
                logger.info(f"Redirecting ir_privado to: {redirect_url}")
                await query.answer(url=redirect_url)
            else:
                logger.warning("No bot_username found, cannot redirect.")
                await query.answer()  # Fallback

        except Exception as e:
            logger.error(f"Error handling ir_privado: {e}")
        return


async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que borra un mensaje."""
    job = context.job
    data = job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception as e:
        logger.debug(f"Error deleting message in job: {e}")


async def donation_timeout_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que cancela el registro de donación por inactividad."""
    job = context.job
    uid = job.data["uid"]
    st = state_manager.get_user_state(uid)

    if not st.get("waiting_for_donation_proof"):
        return

    # Limpiar estado
    st.pop("waiting_for_donation_proof", None)
    st.pop("donation_timeout_job_name", None)

    # Notificar al usuario
    cms = context.application.plugin_manager.get_plugin("custom_messages")
    user = job.data.get("user")

    base_text = "⚠️ <b>Registro de Donación Cancelado</b>\n\nEl tiempo de espera ha expirado."
    text = base_text
    if cms and cms.enabled:
        text = await cms.get_text("donation_cancelled_timeout", user=user)

    try:
        await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"No se pudo notificar timeout de donación a {uid}: {e}")

    # Borrar el mensaje de solicitud si se envió
    msg_id = job.data.get("msg_id")
    if msg_id:
        try:
            await context.bot.delete_message(chat_id=uid, message_id=msg_id)
        except Exception:
            pass


async def cancelar_donacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el botón 'Cancelar Registro' de donación."""
    query = update.callback_query
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    # Verificar si el botón es del usuario dueño
    try:
        target_uid = int(query.data.split("|")[1])
        if uid != target_uid:
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_text = "⚠️ Este botón no es para ti."
            text = base_text
            if cms and cms.enabled:
                text = await cms.get_text("button_unauthorized")
            await query.answer(text, show_alert=True)
            return
    except (ValueError, IndexError):
        pass

    # Limpiar estado
    st.pop("waiting_for_donation_proof", None)

    # Cancelar job de timeout si existe
    job_name = st.pop("donation_timeout_job_name", None)
    if job_name and context.job_queue:
        jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in jobs:
            job.schedule_removal()

    # Notificar y borrar mensaje
    cms = context.application.plugin_manager.get_plugin("custom_messages")
    base_text = "✅ <b>Registro Cancelado</b>\n\nEl registro de tu donación ha sido cancelado."
    text = base_text
    if cms and cms.enabled:
        text = await cms.get_text("donation_cancelled_user", user=update.effective_user)

    try:
        await query.answer("Registro cancelado.")
        await query.edit_message_text(text, parse_mode="HTML")
    except Exception:
        try:
            await context.bot.send_message(chat_id=uid, text=text, parse_mode="HTML")
            await query.message.delete()
        except Exception:
            pass


def register_handlers(app):
    # CallbackQuery handlers
    app.add_handler(CallbackQueryHandler(set_destino, pattern="^destino\\|"))
    app.add_handler(CallbackQueryHandler(ver_catalogo_normal, pattern="^ver_catalogo_normal$"))
    app.add_handler(CallbackQueryHandler(buscar_epub, pattern="^buscar$"))
    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(col\\||lib\\||nav\\||subir_nivel|volver_colecciones|volver_ultima|cerrar|cerrar_donacion\\||cancelar_donacion\\||descargar_epub|preparar_post_fb|publicar_fb|descartar_fb|publish_target\\||set_publish_temp\\||notificar_donacion|ir_privado\\|)",
        )
    )
    # Texto libre handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_destino))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_text))
