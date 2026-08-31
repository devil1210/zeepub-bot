# handlers/commands/admin_callbacks.py
"""
Manejador especializado de callbacks para el Panel de Administración y Herramientas del Sistema.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from services.library_ui_service import (
    check_is_admin_or_staff,
    ejecutar_admin_scan,
    ejecutar_admin_update,
    mostrar_panel_admin,
)
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


async def handle_admin_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> bool:
    """Procesa callbacks dirigidos al panel de administración. Retorna True si fue manejado."""
    query = update.callback_query
    if not query:
        return False

    uid = update.effective_user.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)

    if not is_staff:
        await query.answer("🚫 Acceso denegado. Solo administradores.", show_alert=True)
        return True

    if data in ("admin_panel", "admin"):
        await query.answer()
        await mostrar_panel_admin(update, context, force_new=False)
        return True

    if data.startswith("admin_act|"):
        act = data.split("|")[1]

        if act == "scan":
            await ejecutar_admin_scan(update, context)
            return True

        elif act == "update":
            await ejecutar_admin_update(update, context)
            return True

        elif act == "stats":
            await query.answer()
            from plugins.stats_plugin import StatsPlugin

            stats_p = StatsPlugin()
            stats_p.enabled = True
            await stats_p.stats(update, context)
            return True

        elif act == "id":
            user = update.effective_user
            chat = update.effective_chat
            cid = chat.id if chat else 0
            username = f"@{user.username}" if user and user.username else user.first_name

            msg = (
                f"🆔 <b>Identidad de Sesión</b>\n\n"
                f"• <b>Usuario:</b> {username}\n"
                f"• <b>User ID:</b> <code>{uid}</code>\n"
                f"• <b>Chat ID:</b> <code>{cid}</code>\n"
            )
            if thread_id:
                msg += f"• <b>Thread ID:</b> <code>{thread_id}</code>\n"

            await query.answer()
            await context.bot.send_message(
                chat_id=cid,
                text=msg,
                parse_mode="HTML",
                message_thread_id=thread_id,
            )
            return True

        elif act == "integrity":
            await query.answer("🔍 Verificando integridad de la biblioteca...", show_alert=False)
            from sqlalchemy import text
            from core.postgres_manager import pg_manager

            try:
                async with pg_manager.get_session() as session:
                    res_dup = await session.execute(
                        text("""
                            SELECT hash_md5, COUNT(*) as c
                            FROM books
                            WHERE hash_md5 IS NOT NULL
                            GROUP BY hash_md5
                            HAVING COUNT(*) > 1
                        """)
                    )
                    dups = res_dup.fetchall()

                    res_orph = await session.execute(
                        text("""
                            SELECT COUNT(*)
                            FROM books b
                            LEFT JOIN series s ON b.series_id = s.id
                            WHERE s.id IS NULL
                        """)
                    )
                    orphans = res_orph.scalar() or 0

                msg = (
                    f"🧹 <b>Diagnóstico de Integridad • ZeePubs</b>\n\n"
                    f"• <b>Grupos de Duplicados:</b> {len(dups)}\n"
                    f"• <b>Libros Huérfanos:</b> {orphans}\n"
                    f"• <b>Estado General:</b> {'✅ Óptimo' if len(dups) == 0 and orphans == 0 else '⚠️ Requiere revisión'}\n"
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=msg,
                    parse_mode="HTML",
                    message_thread_id=thread_id,
                )
            except Exception as e:
                logger.error(f"Error verificando integridad: {e}")
                await query.answer(f"❌ Error: {e}", show_alert=True)
            return True

    return False
