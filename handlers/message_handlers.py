# handlers/message_handlers.py

import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.opds_service import get_cached_feed, mostrar_colecciones

# from utils.http_client import parse_feed_from_url
from utils.helpers import build_search_url, get_thread_id

logger = logging.getLogger(__name__)


async def recibir_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja mensajes de texto cuando se espera input del usuario."""
    # Ignorar mensajes editados o vacíos
    if not update.message or not update.effective_user:
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
                msg = await cms.get_text(
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

    # Handle custom suggestion responses
    if st.get("waiting_for_suggestion_response"):
        target_user_id = st.get("waiting_for_suggestion_response")
        custom_response = text
        original_msg_id = st.get("suggestion_original_message_id")
        original_chat_id = st.get("suggestion_original_chat_id")
        original_text = st.get("suggestion_original_text")

        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_text = f"💬 Respuesta a tu Sugerencia\n\n{custom_response}"
        response_text = base_text
        if cms and cms.enabled:
            response_text = await cms.get_text(
                "suggestion_custom_response", Respuesta=custom_response
            )

        try:
            await context.bot.send_message(
                chat_id=target_user_id, text=response_text, parse_mode="HTML"
            )

            # Update original message
            if original_msg_id and original_chat_id and original_text:
                try:
                    # Truncate if too long
                    response_preview = (
                        custom_response[:100] + "..."
                        if len(custom_response) > 100
                        else custom_response
                    )
                    await context.bot.edit_message_text(
                        chat_id=original_chat_id,
                        message_id=original_msg_id,
                        text=original_text
                        + f"\n\n💬 <b>Respuesta enviada:</b> {response_preview}",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.warning(f"No se pudo actualizar mensaje original: {e}")

            await update.message.reply_text("✅ Respuesta enviada al usuario.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error enviando respuesta: {e}")

        # Clear state
        st.pop("waiting_for_suggestion_response", None)
        st.pop("suggestion_original_message_id", None)
        st.pop("suggestion_original_chat_id", None)
        st.pop("suggestion_original_text", None)
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

        # API 9.3: Routing to Búsquedas topic in private forums
        effective_thread_id = thread_id
        if chat_type == "private":
            from services.topic_service import topic_service

            t_id = await topic_service.get_topic_id(uid, "busquedas")
            if t_id:
                effective_thread_id = t_id

        st["message_thread_id"] = effective_thread_id

        # API 9.3: Streaming feedback
        from utils.streaming import send_message_draft

        cms = context.application.plugin_manager.get_plugin("custom_messages")

        draft_text = f"🔎 Buscando en catálogos: <i>{html.escape(text)}</i>..."
        if cms and cms.enabled:
            draft_text = await cms.get_text(
                "search_streaming_feedback", Termino=html.escape(text)
            )

        draft_id = await send_message_draft(
            context.bot,
            update.effective_chat.id,
            draft_text,
            message_thread_id=effective_thread_id,
        )

        search_url = build_search_url(text, uid)
        logger.debug(f"URL de búsqueda: {search_url}")
        feed = await get_cached_feed(search_url)

        # Finalize draft by deleting it (or resolving it)
        if draft_id:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id, message_id=draft_id
                )
            except Exception:
                pass

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
                text_no_results = await cms.get_text(
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
            await cms.get_text("private_default_fallback")
            if (cms and cms.enabled)
            else base_fallback
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=text_fallback, parse_mode="HTML"
        )


async def handle_json_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la subida del archivo result.json para importar historial."""
    if not update.message or not update.effective_user:
        return

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

        await asyncio.to_thread(os.remove, file_path)

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


async def handle_donation_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la recepción de comprobantes de donación (Foto o Documento)."""
    if not update.effective_user:
        return

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    if not st.get("waiting_for_donation_proof"):
        return

    # Validar que sea chat privado
    if update.effective_chat.type != "private":
        return

    # Verificar contenido
    file_obj = None

    if update.message.photo:
        file_obj = update.message.photo[-1]  # Mejor calidad
        type_str = "Foto"
    elif update.message.document:
        file_obj = update.message.document
        type_str = "Documento"

    if not file_obj:
        cms = context.application.plugin_manager.get_plugin("custom_messages")
        base_text = "❌ Por favor envía una imagen o un archivo PDF."
        text = base_text
        if cms and cms.enabled:
            text = await cms.get_text("donation_proof_invalid_format")
        await update.message.reply_text(text)
        return

    # Limpiar estado
    st.pop("waiting_for_donation_proof", None)

    # Cancelar job de timeout si existe
    job_name = st.pop("donation_timeout_job_name", None)
    if job_name and context.job_queue:
        jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in jobs:
            job.schedule_removal()
            logger.debug(f"Donation timeout job {job_name} cancelled (proof received).")

    # Notificar usuario
    cms = context.application.plugin_manager.get_plugin("custom_messages")
    base_success = (
        "✅ <b>Comprobante recibido</b>\n\n"
        "Hemos enviado tu comprobante a los administradores para su verificación.\n"
        "Te avisaremos cuando tu nivel sea actualizado.\n"
        "¡Gracias por tu apoyo! ❤️"
    )
    text_success = base_success
    if cms and cms.enabled:
        text_success = await cms.get_text(
            "donation_proof_received", user=update.effective_user
        )

    await update.message.reply_text(text_success, parse_mode="HTML")

    # Notificar Admins
    user = update.effective_user
    username = f"@{user.username}" if user.username else "Sin alias"

    admin_caption = (
        f"💰 <b>Nueva Donación (con Comprobante)</b>\n\n"
        f"👤 <b>Usuario:</b> {user.first_name} ({username})\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"📎 <b>Tipo:</b> {type_str}\n\n"
        f"Por favor verifica el documento adjunto."
    )

    for admin_id in config.ADMIN_USERS:
        try:
            # Reenviar el mensaje o enviar una copia?
            # copy_message es mejor para mantener el contenido
            await context.bot.copy_message(
                chat_id=admin_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                caption=admin_caption,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Error forwarding proof to admin {admin_id}: {e}")
