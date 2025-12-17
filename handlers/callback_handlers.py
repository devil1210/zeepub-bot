# handlers/callback_handlers.py

import re
import uuid
import logging
from urllib.parse import unquote, urlparse
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from core.state_manager import state_manager
from services.opds_service import mostrar_colecciones, buscar_zeepubs_directo
from services.telegram_service import publicar_libro
from config.config_settings import config
from utils.helpers import find_zeepubs_destino
from utils.http_client import parse_feed_from_url

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
        await query.answer("✅ Destino seleccionado")

        # Si no es admin, ir directamente a ZeePubs [ES]
        if uid not in config.ADMIN_USERS:
            await buscar_zeepubs_directo(update, context, uid)
        else:
            await mostrar_colecciones(
                update, context, st["opds_root"], from_collection=False
            )
        return

    # Destino manual
    if destino == "otro":
        st["esperando_destino_manual"] = True
        await query.edit_message_text("✏️ Escribe @usuario o chat_id para publicar:")
        return


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
    # Mostrar colecciones Evil con el nuevo destino
    await mostrar_colecciones(update, context, st["opds_root"], from_collection=False)


async def buscar_epub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    chat = update.effective_chat

    # En chats privados, siempre usar texto libre
    if chat.type == "private":
        st["esperando_busqueda"] = True
        await query.edit_message_text("🔍 Escribe parte del título del EPUB:")
        return

    # En grupos, verificar si el bot es administrador
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        is_admin = bot_member.status in ["administrator", "creator"]
    except Exception:
        is_admin = False

    if is_admin:
        # Bot es admin: puede recibir mensajes normales
        st["esperando_busqueda"] = True
        await query.edit_message_text("🔍 Escribe parte del título del EPUB:")
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
            text_instr = await cms.get_text(
                "search_instructions_legacy"
            )

        await query.edit_message_text(
            text_instr,
            parse_mode="HTML",
        )


async def handle_search_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura texto tras /search o tras inline 'Buscar EPUB'."""
    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    if not st.get("esperando_busqueda"):
        return

    termino = update.message.text.strip()
    st.pop("esperando_busqueda", None)
    # Lanza búsqueda y muestra resultados
    await buscar_zeepubs_directo(update, context, uid, termino)


async def abrir_zeepubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await buscar_zeepubs_directo(update, context, update.effective_user.id)


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
        return

    # Selección de colección
    if data.startswith("col|"):
        idx = int(data.split("|", 1)[1])
        col = st["colecciones"].get(idx)
        if col:
            titulo_col = col.get("titulo", "").lower()

            # Si no es admin y es "Todas las bibliotecas", saltar a ZeePubs [ES] directamente
            if uid not in config.ADMIN_USERS and "todas las bibliotecas" in titulo_col:
                from services.opds_service import get_zeepubs_first_library

                root_page = {
                    "titulo": "📚 Todas las bibliotecas",
                    "url": st.get("opds_root"),
                    "type": "root",
                }
                st["historial"] = [root_page]
                st["titulo"] = "📁 Biblioteca ZeePubs"

                zeepubs_first_url = await get_zeepubs_first_library(st.get("opds_root"))
                await mostrar_colecciones(
                    update, context, zeepubs_first_url, from_collection=True
                )
            else:
                # Navegar normalmente a la colección (para admins o colecciones que no sean "Todas las bibliotecas")
                current_page = {
                    "titulo": st.get("titulo", ""),
                    "url": st.get("url", ""),
                    "type": "collection",
                }
                if "historial" not in st:
                    st["historial"] = []
                st["historial"].append(current_page)

                st["titulo"] = f"📁 {col['titulo']}"
                st["url"] = col["href"]
                await mostrar_colecciones(
                    update, context, col["href"], from_collection=True
                )
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
        libro = st["libros"].get(key)
        if not libro:
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
                await context.bot.delete_message(
                    chat_id=chat_origen, message_id=query.message.message_id
                )
            except Exception:
                logger.debug("No se pudo borrar menú")
            try:
                from utils.helpers import get_thread_id

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
                from services.telegram_service import _publish_choice_facebook

                await _publish_choice_facebook(update, context, uid)
                return
            elif default_target == "telegram":
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
                        await query.edit_message_text(
                            f"✅ Publicado: {libro['titulo']}"
                        )
                    except Exception:
                        logger.debug("Error al editar confirmación")
                return
            # If no temp target is set, fall through to normal behavior (no menu)

        # Publicar EPUB (non-publishers or publisher with no temp)
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
                await query.edit_message_text(f"✅ Publicado: {libro['titulo']}")
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
            from services.telegram_service import _publish_choice_facebook

            await _publish_choice_facebook(update, context, uid)
        elif choice == "telegram":
            # Continue publishing using stored pending data
            pending = st.get("pending_pub_book")
            if not pending:
                await query.answer("No hay publicación pendiente.")
            else:
                # use the module-level publicar_libro imported at top
                # Clear pending flag then call publicar_libro to proceed
                menu_prep = st.pop("pending_pub_menu_prep", None)
                st.pop("pending_pub_book", None)
                # Call publicar_libro using stored href/portada/title
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
                await query.edit_message_text("⛔ Publicación cancelada.")
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
                await query.answer("Opción inválida")
            except Exception:
                pass
            return
        if choice == "none":
            st.pop("publish_target_temp", None)
            text = "⚪ Preferencia temporal de publicación descartada."
        else:
            # Set one-time publish target that will be popped at next selection
            st["publish_target_temp"] = choice
            text = (
                f"✅ Publicación temporal establecida para el próximo libro: {choice}."
            )

        # For non-admin publishers, proceed to show the normal collections
        # menu now (but don't ask for Evil destination). If the user picked
        # Facebook, assume publishing in the current chat.
        if uid not in config.ADMIN_USERS:
            root = config.OPDS_ROOT_START
            st["opds_root"] = root
            st["opds_root_base"] = root
            st["historial"] = []
            st["ultima_pagina"] = root
            if choice == "facebook":
                st["destino"] = update.effective_chat.id
                st["chat_origen"] = update.effective_chat.id
            await mostrar_colecciones(update, context, root, from_collection=False)
            return

        # If the user is an admin+publisher, choose subsequent behavior now:
        # - If they picked 'telegram' we configure Evil root and show the destination selector.
        # - If they picked 'facebook' assume "aquí" and enter Evil root directly
        #   (publisher flow will create FB preview on selection). Non-admin
        #   publishers continue to the normal start flow.
        if uid in config.ADMIN_USERS:
            if choice == "telegram":
                # Configure Evil root BEFORE showing destination selector
                st["opds_root"] = config.OPDS_ROOT_EVIL
                st["opds_root_base"] = config.OPDS_ROOT_EVIL
                st["historial"] = []
                st["ultima_pagina"] = config.OPDS_ROOT_EVIL

                keyboard = [
                    [InlineKeyboardButton("📍 Aquí", callback_data="destino|aqui")],
                    [
                        InlineKeyboardButton(
                            "📣 BotTest", callback_data="destino|@ZeePubBotTest"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📣 ZeePubs", callback_data="destino|@ZeePubs"
                        )
                    ],
                    [InlineKeyboardButton("✏️ Otro", callback_data="destino|otro")],
                ]
                try:
                    await query.edit_message_text(
                        text="🔧 Modo Evil: ¿Dónde quieres publicar?",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                except Exception:
                    try:
                        await query.answer("🔧 Modo Evil: ¿Dónde quieres publicar?")
                    except Exception:
                        pass
                return

            if choice == "facebook":
                # Admin+publisher; assume publishing in this chat and enter Evil root
                st["opds_root"] = config.OPDS_ROOT_EVIL
                st["opds_root_base"] = config.OPDS_ROOT_EVIL
                st["historial"] = []
                st["ultima_pagina"] = config.OPDS_ROOT_EVIL
                st["destino"] = update.effective_chat.id
                st["chat_origen"] = update.effective_chat.id
                try:
                    await query.edit_message_text(
                        "✅ Publicación temporal en Facebook seleccionada — entrando a Evil (publicación en este chat)."
                    )
                except Exception:
                    try:
                        await query.answer(
                            "🔧 Publicación temporal en Facebook seleccionada — entrando a Evil"
                        )
                    except Exception:
                        pass
                # show evil collections directly
                await mostrar_colecciones(
                    update, context, st["opds_root"], from_collection=False
                )
                return
        try:
            await query.edit_message_text(text)
        except Exception:
            try:
                await query.answer(text)
            except Exception:
                logger.debug("Could not send set_publish_temp response")
        return

    # Subir nivel (usar historial para ir al nivel anterior)
    if data == "subir_nivel":
        if "historial" not in st:
            st["historial"] = []

        if st["historial"]:
            last_page = st["historial"].pop()
            if last_page and last_page.get("url"):
                st["titulo"] = last_page["titulo"]
                st["url"] = last_page["url"]
                await mostrar_colecciones(
                    update, context, last_page["url"], from_collection=True
                )
            else:
                root = st.get("opds_root_base") or st.get("opds_root")
                st["titulo"] = "📚 Categorías"
                st["url"] = root
                await mostrar_colecciones(update, context, root, from_collection=False)
        else:
            root = st.get("opds_root_base") or st.get("opds_root")
            st["titulo"] = "📚 Categorías"
            st["url"] = root
            await mostrar_colecciones(update, context, root, from_collection=False)
        return

    # Navegación paginada (solo dentro de la misma página, sin historial)
    if data.startswith("nav|"):
        direction = data.split("|", 1)[1]
        nav_url = st.get("nav", {}).get(direction)
        if nav_url:
            st["url"] = nav_url
            await mostrar_colecciones(update, context, nav_url, from_collection=False)
        else:
            await query.answer("🚫 No hay más páginas")
        return

    # Volver a categorías raíz
    if data == "volver_colecciones":
        root = st.get("opds_root_base") or st.get("opds_root")
        st["historial"] = []
        st["titulo"] = "📚 Categorías"
        st["url"] = root
        await mostrar_colecciones(update, context, root, from_collection=False)
        return

    # Volver a última página donde se listaban los EPUB
    if data == "volver_ultima":
        # Borrar mensaje de botones (el actual)
        try:
            await query.message.delete()
        except Exception:
            pass

        last_url = st.get("ultima_pagina")
        if last_url:
            # Opcional: Si también guardas el título anterior, úsalo aquí
            st["titulo"] = "📚 Última página"
            st["url"] = last_url
            # Usar new_message=True para que no borre el mensaje del libro
            await mostrar_colecciones(
                update, context, last_url, from_collection=True, new_message=True
            )
        else:
            # Si no hay última página guardada, usar historial como antes
            if "historial" not in st:
                st["historial"] = []
            if st["historial"]:
                last_page = st["historial"].pop()
                if last_page and last_page.get("url"):
                    st["titulo"] = last_page["titulo"]
                    st["url"] = last_page["url"]
                    await mostrar_colecciones(
                        update,
                        context,
                        last_page["url"],
                        from_collection=True,
                        new_message=True,
                    )
                else:
                    root = st.get("opds_root_base") or st.get("opds_root")
                    st["titulo"] = "📚 Categorías"
                    st["url"] = root
                    await mostrar_colecciones(
                        update, context, root, from_collection=False, new_message=True
                    )
            else:
                root = st.get("opds_root_base") or st.get("opds_root")
                st["titulo"] = "📚 Categorías"
                st["url"] = root
                await mostrar_colecciones(
                    update, context, root, from_collection=False, new_message=True
                )
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

        await descargar_epub_pendiente(
            update, context, uid, job_queue=context.job_queue
        )
        return

    # Facebook handlers
    if data == "preparar_post_fb":
        from services.telegram_service import preparar_post_facebook

        await preparar_post_facebook(update, context, uid)
        try:
            await query.answer()
        except Exception as e:
            logger.debug("Could not answer callback for preparar_post_fb: %s", e)
        return

    if data == "publicar_fb":
        from services.telegram_service import publicar_facebook_action

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
            await query.answer("🗑️ Descartado")
        except Exception as e:
            logger.debug("Could not discard FB preview buttons: %s", e)
        return
    if data == "notificar_donacion":
        try:
            # 1. Establecer estado esperando comprobante
            uid = update.effective_user.id
            st = state_manager.get_user_state(uid)
            st["waiting_for_donation_proof"] = True

            cms = context.application.plugin_manager.get_plugin("custom_messages")

            # Intentar borrar el mensaje original para limpieza
            try:
                await query.message.delete()
            except Exception:
                pass

            # 2. Verificar si es chat privado
            if update.effective_chat.type != "private":
                try:
                    bot_username = context.bot.username
                    keyboard = [[InlineKeyboardButton("📩 Enviar comprobante aquí", url=f"https://t.me/{bot_username}")]]

                    await query.answer("✅ Solicitud registrada.")
                    # Usar explicitly el chat_id del mensaje original para asegurar que se envía al mismo grupo
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"👋 Hola {update.effective_user.mention_html()},\n\nPara proteger tu privacidad, por favor envíame el comprobante a mi chat privado pulsando el botón de abajo.",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Error answering query in group: {e}")
                return

            # 3. Es chat privado - Mostrar instrucciones directamente
            # Enviamos mensaje nuevo porque borramos el anterior
            base_request = (
                "🧾 <b>Comprobante Requerido</b>\n\n"
                "Por favor, envía una <b>captura de pantalla</b> o <b>archivo PDF</b> de tu comprobante de donación.\n"
                "Lo revisaremos para actualizar tu nivel."
            )
            text_request = base_request
            if cms and cms.enabled:
                text_request = await cms.get_text("donation_proof_request", user=update.effective_user)

            await query.answer()
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_request,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error handling notificar_donacion: {e}", exc_info=True)
            try:
                await query.answer("❌ Ocurrió un error al procesar tu solicitud.", show_alert=True)
            except Exception:
                pass
        return


def register_handlers(app):
    # CallbackQuery handlers
    app.add_handler(CallbackQueryHandler(set_destino, pattern="^destino\\|"))
    app.add_handler(CallbackQueryHandler(buscar_epub, pattern="^buscar$"))
    app.add_handler(
        CallbackQueryHandler(
            button_handler,
            pattern="^(col\\||lib\\||nav\\||subir_nivel|volver_colecciones|volver_ultima|cerrar|descargar_epub|preparar_post_fb|publicar_fb|descartar_fb|publish_target\\||set_publish_temp\\||notificar_donacion)",
        )
    )
    # Texto libre handlers
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_destino)
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_text))
