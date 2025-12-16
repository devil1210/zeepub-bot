# handlers/message_handlers.py

import logging
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from core.state_manager import state_manager
from services.opds_service import mostrar_colecciones, get_cached_feed
from config.config_settings import config
from utils.helpers import build_search_url

# from utils.http_client import parse_feed_from_url
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


async def recibir_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto cuando se espera input del usuario."""
    # Ignorar mensajes editados o vacíos
    if not update.message:
        return

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)
    text = update.message.text.strip()
    chat_type = update.effective_chat.type

    thread_id = get_thread_id(update)

    # ⚠️ OPTIMIZACIÓN: Solo chequear ban en chats privados
    # Los grupos/canales tienen su propia moderación
    if chat_type == "private":
        from services.user_service import get_effective_user

        user_info = await get_effective_user(uid)
        if user_info.get("role") == "banned":
            expires_at = user_info.get("expires_at")

            # Template System
            cms = context.application.plugin_manager.get_plugin("custom_messages")

            exp_str = expires_at.strftime("%Y-%m-%d %H:%B") if expires_at else None
            default_msg_template = "⛔ Estás <b>baneado</b> del bot.{{if Fecha}} Hasta: <b>[Fecha]</b>{{endif}}"

            if cms and cms.enabled:
                msg = cms.get_text(
                    "banned_message",
                    user=update.effective_user,
                    Fecha=exp_str,
                )
            else:
                msg = (
                    default_msg_template.replace("{{if Fecha}}", "")
                    .replace("{{endif}}", "")
                    .replace("<b>[Fecha]</b>", f"<b>{exp_str}</b>" if exp_str else "")
                )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return

    # 1) Contraseña para modo 'evil'
    if st.get("esperando_password"):
        st["esperando_password"] = False
        if text == config.get_six_hour_password():
            keyboard = [
                [InlineKeyboardButton("📍 Aquí", callback_data="destino|aqui")],
                [
                    InlineKeyboardButton(
                        "📢 BotTest", callback_data="destino|@ZeePubBotTest"
                    )
                ],
                [InlineKeyboardButton("📢 ZeePubs", callback_data="destino|@ZeePubs")],
                [InlineKeyboardButton("✏️ Otro", callback_data="destino|otro")],
            ]

            # Template System
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_text = "✅ Contraseña correcta. Elige destino:"
            text_success = (
                cms.get_text("evil_password_success")
                if (cms and cms.enabled)
                else base_text
            )

            # Editar el prompt original si se guardó
            msg_id = st.get("msg_esperando_pwd")
            if msg_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=msg_id,
                        text=text_success,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="HTML",
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text_success,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        message_thread_id=thread_id,
                        parse_mode="HTML",
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text_success,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    message_thread_id=thread_id,
                    parse_mode="HTML",
                )
        else:
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_fail = "❌ Contraseña incorrecta."
            text_fail = (
                cms.get_text("evil_password_fail")
                if (cms and cms.enabled)
                else base_fail
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_fail,
                message_thread_id=thread_id,
                parse_mode="HTML",
            )
        return

    # 2) Destino manual
    if st.get("esperando_destino_manual"):
        st["esperando_destino_manual"] = False
        st["destino"] = text
        await mostrar_colecciones(
            update, context, st["opds_root"], from_collection=False
        )
        return

    # 3) Búsqueda de EPUB
    if st.get("esperando_busqueda"):
        logger.debug(f"Usuario {uid} buscando: {text}")
        st["esperando_busqueda"] = False
        st["message_thread_id"] = thread_id  # Guardar thread_id
        search_url = build_search_url(text, uid)
        logger.debug(f"URL de búsqueda: {search_url}")
        feed = await get_cached_feed(search_url)
        if not feed or not getattr(feed, "entries", []):
            keyboard = [
                [InlineKeyboardButton("🔄 Volver a buscar", callback_data="buscar")],
                [
                    InlineKeyboardButton(
                        "📚 Ir a colecciones", callback_data="volver_colecciones"
                    )
                ],
            ]

            # Template System
            cms = context.application.plugin_manager.get_plugin("custom_messages")
            base_no_results = f"🔍 No se encontraron resultados para: {text}"

            # Using safe helper for text
            safe_term = html.escape(text)
            text_no_results = base_no_results  # Default

            if cms and cms.enabled:
                # We can provide [Termino] as replacement
                text_no_results = cms.get_text(
                    "search_no_results",
                    Termino=safe_term,
                )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_no_results,
                reply_markup=InlineKeyboardMarkup(keyboard),
                message_thread_id=thread_id,
                parse_mode="HTML",
            )
        else:
            logger.debug(f"Encontrados {len(feed.entries)} resultados")
            await mostrar_colecciones(
                update, context, search_url, from_collection=False
            )
        return

    # 4) Cualquier otro texto - solo responder en chats privados
    if chat_type == "private":
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_fallback = "Usa /start para comenzar o selecciona una opción del menú."
        text_fallback = (
            cms.get_text("private_default_fallback")
            if (cms and cms.enabled)
            else base_fallback
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=text_fallback, parse_mode="HTML"
        )


async def handle_json_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la subida del archivo result.json para importar historial."""
    document = update.message.document
    if not document:
        return

    # Verificar nombre de archivo
    if not (
        document.file_name == "result.json" or document.mime_type == "application/json"
    ):
        return

    # Verificar admin (opcional, pero recomendado)
    uid = update.effective_user.id
    if uid not in config.ADMIN_USERS:
        return

    # Verificar estado activo
    st = state_manager.get_user_state(uid)
    if not st.get("waiting_for_history_json"):
        # Ignorar silenciosamente si no se activó el comando
        return

    # Limpiar estado
    st["waiting_for_history_json"] = False

    status_msg = await update.message.reply_text(
        "⏳ Procesando archivo de historial..."
    )

    try:
        # Descargar archivo
        new_file = await document.get_file()
        file_path = f"/tmp/{document.file_unique_id}.json"
        await new_file.download_to_drive(file_path)

        # Procesar en un thread aparte para no bloquear
        import asyncio
        from services.history_service import process_history_json

        loop = asyncio.get_running_loop()
        stats = await loop.run_in_executor(None, process_history_json, file_path)

        # Reportar
        import os

        os.remove(file_path)

        text = (
            f"✅ Importación completada.\n\n"
            f"Total mensajes escaneados: {stats['total']}\n"
            f"Libros importados: {stats['imported']}\n"
            f"Errores: {stats['errors']}"
        )
        await status_msg.edit_text(text)

    except Exception as e:
        logger.error(f"Error processing JSON upload: {e}")
        await status_msg.edit_text(f"❌ Error al procesar el archivo: {e}")
