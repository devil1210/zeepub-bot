# services/library_ui/admin_views.py
"""
Vistas para el Panel de Administración y Mantenimiento usando Rich Messages.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.library_service import LibraryService
from services.rich_message_service import RichMessageService
from utils.helpers import get_last_commit_message, get_thread_id

from .builders import (
    build_admin_panel_rich_blocks,
    build_admin_scan_result_blocks,
)
from .info_views import check_is_admin_or_staff

logger = logging.getLogger(__name__)


async def mostrar_panel_admin(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra el panel de control administrativo interactivo en Rich Message."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        if update.callback_query:
            await update.callback_query.answer("🚫 Acceso restringido a Administradores.", show_alert=True)
        elif update.message:
            await update.message.reply_text("🚫 Acceso restringido a Administradores.", message_thread_id=thread_id)
        return

    # Obtener estadísticas en tiempo real
    stats = await LibraryService.get_library_stats()
    git_hash = get_last_commit_message() or "v3.6.0"

    blocks = build_admin_panel_rich_blocks(stats=stats, git_hash=git_hash)

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
            logger.debug(f"[mostrar_panel_admin] No se pudo editar in-place: {e}")

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )


async def ejecutar_admin_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta el escaneo de la biblioteca local y muestra el resultado en Rich Message."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        if update.callback_query:
            await update.callback_query.answer("🚫 Acceso restringido a Administradores.", show_alert=True)
        elif update.message:
            await update.message.reply_text("🚫 Acceso restringido a Administradores.", message_thread_id=thread_id)
        return

    # Feedback inmediato
    if update.callback_query:
        await update.callback_query.answer("🔄 Iniciando escaneo de la biblioteca...", show_alert=False)

    loading_blocks = [
        {"type": "heading", "size": 2, "text": "🔄 Escaneando Biblioteca • ZeePubs"},
        {"type": "paragraph", "text": "Procesando archivos EPUB locales, metadatos y portadas en segundo plano...\n\n<i>Esto puede tardar unos segundos.</i>"},
    ]
    if update.callback_query:
        try:
            await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=loading_blocks,
            )
        except Exception:
            pass

    from services.scanner_service import ScannerService

    scanner = ScannerService()
    results = await scanner.sync_all(force_scan=True)

    result_blocks = build_admin_scan_result_blocks(results or {})

    if update.callback_query:
        try:
            await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=result_blocks,
            )
            return
        except Exception:
            pass

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=result_blocks,
        message_thread_id=thread_id,
    )


async def ejecutar_admin_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica e invoca la actualización del bot con feedback en tiempo real."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        if update.callback_query:
            await update.callback_query.answer("🚫 Acceso restringido a Administradores.", show_alert=True)
        elif update.message:
            await update.message.reply_text("🚫 Acceso restringido a Administradores.", message_thread_id=thread_id)
        return

    if update.callback_query:
        await update.callback_query.answer("⏳ Comprobando versión remota...", show_alert=False)

    from plugins.system_manager_plugin import SystemManagerPlugin

    sys_plugin = SystemManagerPlugin()
    local_hash, remote_hash = await sys_plugin._get_git_hashes()

    is_up_to_date = local_hash == remote_hash and local_hash != "Desconocido"

    update_blocks = [
        {"type": "heading", "size": 2, "text": "🚀 Actualización del Sistema • ZeePubs"},
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [{"text": "🔹 Versión Local", "align": "left"}, {"text": f"<code>{local_hash[:8]}</code>", "align": "left"}],
                [{"text": "🔸 Versión Remota", "align": "left"}, {"text": f"<code>{remote_hash[:8]}</code>", "align": "left"}],
                [{"text": "📊 Estado", "align": "left"}, {"text": "✅ Al día" if is_up_to_date else "⚠️ Actualización disponible", "align": "left"}],
            ],
        },
    ]

    if is_up_to_date:
        update_blocks.append({
            "type": "paragraph",
            "text": "El bot ya está ejecutando la última versión del repositorio.",
        })
        update_blocks.append({
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🛠️ Panel Admin", "callback_data": "admin_panel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        })
    else:
        update_blocks.append({
            "type": "paragraph",
            "text": "Se ha detectado una nueva versión en GitHub. Iniciando sincronización...",
        })
        from services.maintenance_service import trigger_watchtower_update

        success, msg = await trigger_watchtower_update()
        update_blocks.append({
            "type": "paragraph",
            "text": f"<b>Resultado:</b> {msg}",
        })
        update_blocks.append({
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🛠️ Panel Admin", "callback_data": "admin_panel"},
            ],
        })

    if update.callback_query:
        try:
            await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=update_blocks,
            )
            return
        except Exception:
            pass

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=update_blocks,
        message_thread_id=thread_id,
    )
