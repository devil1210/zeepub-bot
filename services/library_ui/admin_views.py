# services/library_ui/admin_views.py
"""
Vistas para el Panel de Administración y Mantenimiento usando Rich Messages.
"""

import logging
import os
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from services.library_service import LibraryService
from services.rich_message_service import RichMessageService
from services.settings_service import get_setting, set_setting
from utils.helpers import get_last_commit_message, get_thread_id

from .builders import (
    build_admin_panel_rich_blocks,
    build_admin_scan_result_blocks,
    build_auto_delete_menu_blocks,
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

    # Obtener estadísticas y configuración
    stats = await LibraryService.get_library_stats()
    git_hash = get_last_commit_message() or "v3.6.0"
    auto_del = get_setting("auto_delete_time", "2") or "2"

    blocks = build_admin_panel_rich_blocks(stats=stats, git_hash=git_hash, auto_del_mins=str(auto_del))

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


async def ejecutar_admin_scan(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    deep_scan: bool = False,
):
    """Ejecuta el escaneo de la biblioteca local (rápido o profundo) y muestra el resultado en Rich Message."""
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

    mode_title = "🔥 Escaneo Profundo" if deep_scan else "⚡ Escaneo Rápido"
    mode_desc = (
        "Re-indexando todos los EPUBs, portadas, metadatos, limpieza de huérfanos y conteos..."
        if deep_scan
        else "Indexando archivos nuevos o modificados en las carpetas locales..."
    )

    # Feedback inmediato
    if update.callback_query:
        await update.callback_query.answer(f"🔄 Iniciando {mode_title.lower()}...", show_alert=False)

    loading_blocks = [
        {"type": "heading", "size": 2, "text": f"🔄 {mode_title} • ZeePubs"},
        {"type": "paragraph", "text": f"{mode_desc}\n\n<i>Esto puede tardar unos segundos.</i>"},
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
    results = await scanner.sync_all(force_scan=deep_scan, soft_scan=not deep_scan)

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

    from services.version_service import VersionService

    v_info = await VersionService.get_version_status()
    branch = v_info.get("branch", "main")
    local_hash = v_info.get("local_hash", "Desconocido")
    remote_hash = v_info.get("remote_hash", "Desconocido")
    is_up_to_date = v_info.get("is_up_to_date", False)
    changelog = v_info.get("changelog", [])

    force_update = False
    if context.args and any("force" in str(a).lower() for a in context.args):
        force_update = True

    update_blocks = [
        {"type": "heading", "size": 2, "text": "🚀 Actualización del Sistema • ZeePubs"},
        {
            "type": "table",
            "is_bordered": True,
            "is_striped": True,
            "is_compact": True,
            "cells": [
                [{"text": "🔹 Rama Activa", "align": "left"}, {"text": str(branch), "align": "left"}],
                [{"text": "🔹 Versión Local", "align": "left"}, {"text": str(local_hash), "align": "left"}],
                [{"text": "🔸 Versión Remota", "align": "left"}, {"text": str(remote_hash), "align": "left"}],
                [{"text": "📊 Estado", "align": "left"}, {"text": "✅ Al día" if is_up_to_date else "⚠️ Actualización disponible", "align": "left"}],
            ],
        },
    ]

    if is_up_to_date and not force_update:
        update_blocks.append(
            RichMessageService.create_paragraph(
                "✅ <b>El sistema ya está completamente actualizado.</b> No se requieren cambios."
            )
        )
        if changelog:
            cl_text = "<b>📌 Últimas mejoras y correcciones aplicadas:</b>\n" + "\n".join(f"• {c}" for c in changelog[:5])
            update_blocks.append(RichMessageService.create_paragraph(cl_text))

        update_blocks.append({
            "type": "buttons",
            "align": "center",
            "buttons": [
                {"text": "🔄 Forzar Actualización", "callback_data": "admin_force_update"},
                {"text": "🛠️ Panel Admin", "callback_data": "admin_panel"},
                {"text": "🏠 Inicio", "callback_data": "volver_menu"},
            ],
        })
    else:
        if force_update:
            update_blocks.append(
                RichMessageService.create_paragraph("⚠️ <b>Actualización Forzada solicitada.</b> Iniciando sincronización...")
            )
        else:
            update_blocks.append(
                RichMessageService.create_paragraph("🚀 <b>Se ha detectado una nueva versión en GitHub.</b> Iniciando sincronización...")
            )

        if changelog:
            cl_text = "<b>✨ Novedades y correcciones en esta actualización:</b>\n" + "\n".join(f"• {c}" for c in changelog[:6])
            update_blocks.append(RichMessageService.create_paragraph(cl_text))

        # Guardar estado para notificar al reiniciar
        msg_id = update.callback_query.message.message_id if update.callback_query else None
        VersionService.save_update_state(chat_id=chat_id, message_id=msg_id, thread_id=thread_id)

        from services.maintenance_service import trigger_watchtower_update

        success, msg = await trigger_watchtower_update()
        update_blocks.append(
            RichMessageService.create_paragraph(f"<b>Resultado:</b> {msg}")
        )
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


async def mostrar_menu_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el submenú interactivo para configurar el tiempo de auto-destrucción."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        if update.callback_query:
            await update.callback_query.answer("🚫 Acceso restringido a Administradores.", show_alert=True)
        return

    curr_str = get_setting("auto_delete_time", "2") or "2"
    try:
        curr_mins = int(curr_str)
    except ValueError:
        curr_mins = 2

    blocks = build_auto_delete_menu_blocks(curr_mins)

    if update.callback_query:
        try:
            await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=update.callback_query.message.message_id,
                blocks=blocks,
            )
            return
        except Exception:
            pass

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )


async def ejecutar_set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, minutes: int):
    """Guarda la nueva configuración de auto-destrucción y actualiza la vista."""
    set_setting("auto_delete_time", str(minutes))
    if update.callback_query:
        await update.callback_query.answer(f"✅ Auto-destrucción configurada a {minutes} min", show_alert=False)
    await mostrar_menu_timer(update, context)


async def ejecutar_admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un backup completo de PostgreSQL y lo envía como documento."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        if update.callback_query:
            await update.callback_query.answer("🚫 Acceso denegado.", show_alert=True)
        return

    if update.callback_query:
        await update.callback_query.answer("⏳ Generando backup de PostgreSQL...", show_alert=False)

    try:
        from services.backup_service import generate_backup_file

        filename = await generate_backup_file()

        if filename and os.path.exists(filename):
            with open(filename, "rb") as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=os.path.basename(filename),
                    caption=f"📦 <b>Backup PostgreSQL • ZeePubs</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            try:
                os.remove(filename)
            except Exception:
                pass
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ No se pudo generar el archivo de backup.",
                message_thread_id=thread_id,
            )
    except Exception as e:
        logger.error(f"Error en ejecutar_admin_backup: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Error generando backup: {e}",
            message_thread_id=thread_id,
        )


async def ejecutar_toggle_grupo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alterna la autorización del grupo actual (Permanente vs Auto-destrucción)."""
    uid = update.effective_user.id
    chat = update.effective_chat
    cid = chat.id if chat else 0
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        if update.callback_query:
            await update.callback_query.answer("🚫 Acceso denegado.", show_alert=True)
        return

    if chat.type not in ["group", "supergroup"]:
        if update.callback_query:
            await update.callback_query.answer(
                "ℹ️ Este comando se utiliza dentro de un grupo para autorizarlo o revocarlo.",
                show_alert=True,
            )
        return

    from services.telegram_service import is_authorized_group
    from repositories.group_settings_repository import group_settings_repo

    currently_auth = is_authorized_group(cid)
    new_state = not currently_auth

    success = await group_settings_repo.set_authorized(cid, new_state)

    if success:
        if new_state:
            msg = f"🏢 <b>¡Grupo Autorizado!</b>\n\nEste grupo (<code>{cid}</code>) ahora tiene modo biblioteca permanente (los libros no se auto-destruyen)."
            alert = "✅ Grupo autorizado exitosamente (permanente)."
        else:
            msg = f"⏳ <b>Autorización Revocada</b>\n\nEste grupo (<code>{cid}</code>) ahora funciona con auto-destrucción de libros."
            alert = "⚠️ Grupo revocado (modo auto-destrucción activo)."

        if update.callback_query:
            await update.callback_query.answer(alert, show_alert=True)
        await context.bot.send_message(chat_id=cid, text=msg, parse_mode="HTML", message_thread_id=thread_id)
    else:
        if update.callback_query:
            await update.callback_query.answer("❌ Error al cambiar estado del grupo.", show_alert=True)
