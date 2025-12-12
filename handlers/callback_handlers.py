# handlers/callback_handlers.py

import re
import uuid
import logging
from urllib.parse import unquote, urlparse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        await query.edit_message_text(
            "🔍 Para buscar, usa el comando:\n\n"
            "<code>/search término de búsqueda</code>\n\n"
            "Ejemplo: <code>/search harry potter</code>",
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
    st = state_manager.get_user_state(uid)

    # Check ban status
    from services.user_service import get_effective_user
    user_info = get_effective_user(uid)
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
        await query.edit_message_text("👋 Gracias por usar el bot.")
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
        user = update.effective_user
        uid = user.id
        username = user.username or "Sin alias"
        full_name = user.full_name

        # Enviar confirmación al usuario
        try:
            await query.answer("¡Gracias! Hemos notificado a los administradores.")
            await query.edit_message_text(
                "✅ <b>Notificación enviada</b>\n\n"
                "Un administrador revisará tu donación pronto y actualizará tu nivel.\n"
                "¡Muchas gracias por tu apoyo! ❤️",
                parse_mode="HTML"
            )
        except Exception:
            pass

        # Notificar a los administradores
        admin_msg = (
            "💰 <b>Nueva Donación Reportada</b>\n\n"
            f"👤 <b>Usuario:</b> {full_name}\n"
            f"🔗 <b>Alias:</b> @{username}\n"
            f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
            "El usuario ha indicado que realizó una donación en Ko-fi.\n"
            "Por favor verifica y usa <code>/nivel</code> (si existiera) o actualiza manualmente."
        )
        for admin_id in config.ADMIN_USERS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=admin_msg, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Error notificando admin {admin_id}: {e}")
        return


async def set_log_level_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback para botones de /setlog."""
    query = update.callback_query
    uid = update.effective_user.id

    if uid not in config.ADMIN_USERS:
        await query.answer("⛔ No tienes permisos.", show_alert=True)
        return

    try:
        data = query.data
        _, level_str = data.split("|", 1)
        level_str = level_str.upper()

        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level_str not in valid_levels:
            await query.answer(f"Nivel inválido: {level_str}", show_alert=True)
            return

        new_level = getattr(logging, level_str)

        # 1. Root logger
        logging.getLogger().setLevel(new_level)

        # 2. Specific loggers
        loggers_to_update = ["uvicorn", "uvicorn.access", "httpx", "telegram", "apscheduler"]
        for logger_name in loggers_to_update:
            logging.getLogger(logger_name).setLevel(new_level)

        logger.log(new_level, f"Log level cambiado a {level_str} por admin {uid} (vía botón)")

        # Update message to reflect active state
        # Rebuild keyboard to show selection? Or just text update.
        # Text update is simpler and cleaner.
        await query.edit_message_text(
            f"✅ Nivel de log cambiado a <b>{level_str}</b>",
            parse_mode="HTML"
        )
        await query.answer(f"Nivel cambiado a {level_str}")

    except Exception as e:
        logger.error(f"Error en set_log_level_callback: {e}", exc_info=True)
        await query.answer("Error al cambiar nivel")


def _get_help_data(uid):
    """Genera la estructura de ayuda y el teclado según el rol del usuario."""
    is_admin = uid in config.ADMIN_USERS
    is_publisher = uid in config.FACEBOOK_PUBLISHERS

    # Definir contenido por categorías
    # Formato: (Comando, Descripción)

    # 1. Inicio (Todos)
    cat_home = [
        ("🚀 /start", "Iniciar el bot"),
        ("ℹ️ /help", "Mostrar esta ayuda"),
        ("📊 /status", "Ver tu estado y descargas"),
        ("❌ /cancel", "Cancelar acción actual"),
        ("☕ /donar", "Link de donación"),
        ("🌟 /niveles", "Info de niveles de usuario"),
    ]

    # 2. Contenido / Herramientas (Mixed)
    cat_content = [
        ("🔍 /search", "Buscar libros"),
    ]
    if is_publisher or is_admin:
        cat_content.extend([
            ("📤 /export_db", "Exportar mapeo de URLs a CSV"),
            ("📈 /status_links", "Ver estado de links acortados"),
            ("📋 /link_list", "Listar links acortados recientes"),
            ("🗑️ /purge_link", "Eliminar un link acortado"),
        ])

    # 3. Admin (Admin only)
    cat_admin = []
    if is_admin:
        cat_admin = [
            ("➕ /add_user", "Agregar/Editar usuario"),
            ("➖ /remove_user", "Remover usuario"),
            ("🏷️ /set_staff_status", "Definir status de Staff"),
            ("⏲️ /set_auto_delete_time", "Tiempo auto-borrado (grupos)"),
            ("📊 /stats <rol>", "Ver stats o listar usuarios"),
            ("🔄 /reset", "Resetear descargas"),
            ("💲 /set_price", "Configurar precio donación"),
            ("🐞 /debug_state", "Info debug usuario"),
            ("🔧 /setlog", "Configurar logs"),
            ("👋 /saludo", "Broadcast mensaje"),
            ("🆔 /id", "Info ID chat/user"),
            ("🆕 /update_system", "Actualizar sistema"),
            ("⚠️ /update_system force", "Forzar reinstalación"),
            ("🧩 /plugins", "Listar plugins"),
        ]

    # 4. Datos / Backup (Admin only)
    cat_data = []
    if is_admin:
        cat_data = [
            ("📦 /backup_db", "Backup DB"),
            ("♻️ /restore_db", "Restaurar DB desde archivo"),
            ("📚 /import_history", "Importar historial JSON"),
            ("📤 /export_history", "Exportar historial CSV"),
            ("🆕 /latest_books", "Ver últimos libros"),
            ("🗑️ /clear_history", "Borrar historial"),
        ]

    return {
        "home": ("🏠 Inicio", cat_home),
        "content": ("📚 Content", cat_content),
        "admin": ("🛠 Admin", cat_admin),
        "data": ("💾 Datos", cat_data),
    }, is_admin, is_publisher


async def help_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la navegación del menú de ayuda."""
    query = update.callback_query
    uid = update.effective_user.id

    try:
        _, target_cat = query.data.split("|", 1)
    except ValueError:
        target_cat = "home"

    help_data, is_admin, is_publisher = _get_help_data(uid)

    # Validar acceso a categorías restringidas
    if target_cat in ("admin", "data") and not is_admin:
        await query.answer("⛔ Acceso restringido", show_alert=True)
        return

    # Construir texto
    cat_title, commands = help_data.get(target_cat, ("Desconocido", []))

    text = f"🤖 <b>Ayuda de ZeePub Bot</b>\n\n"
    text += f"📂 <b>Categoría: {cat_title}</b>\n\n"

    for cmd, desc in commands:
        safe_cmd = cmd.replace("<", "&lt;").replace(">", "&gt;")
        safe_desc = desc.replace("<", "&lt;").replace(">", "&gt;")
        text += f"<b>{safe_cmd}</b>\n   ╰ {safe_desc}\n"

    # Construir teclado
    # Fila 1: Home | Content
    # Fila 2: Admin | Data (Solo si es admin)

    row1 = [
        InlineKeyboardButton("🏠 Inicio", callback_data="help|home"),
        InlineKeyboardButton("📚 Content", callback_data="help|content"),
    ]

    keyboard = [row1]

    if is_admin:
        row2 = [
            InlineKeyboardButton("🛠 Admin", callback_data="help|admin"),
            InlineKeyboardButton("💾 Datos", callback_data="help|data"),
        ]
        keyboard.append(row2)

    # Marcar el botón activo visualmente? (Telegram no soporta 'active' state nativo,
    # pero podríamos cambiar el texto del botón actual, ej: "• Inicio •")
    # Por simplicidad, dejamos los botones fijos.

    # Botón cerrar
    keyboard.append([InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")])

    try:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        # Ignore "Message is not modified"
        if "Message is not modified" in str(e):
            pass
        else:
            logger.warning(f"Error updating help menu: {e}")

    try:
        await query.answer()
    except Exception:
        pass


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
