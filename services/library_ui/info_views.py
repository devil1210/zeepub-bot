# services/library_ui/info_views.py
"""
Vistas para Información, Ayuda, Donaciones y Reglas usando Rich Messages.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config.config_settings import config
from services.rich_message_service import RichMessageService
from utils.helpers import get_thread_id

from .builders import (
    build_donations_rich_blocks,
    build_help_rich_blocks,
    build_rules_rich_blocks,
)

logger = logging.getLogger(__name__)


async def check_is_admin_or_staff(uid: int, tg_user=None) -> bool:
    """Verifica si el usuario tiene privilegios de Admin o Staff/Publicador."""
    try:
        from services.user_service import get_user_role

        role = await get_user_role(uid)
        if role in ["admin", "staff", "publicador", "VIP", "editor"]:
            return True
    except Exception:
        pass

    if uid in getattr(config, "ADMIN_USERS", []):
        return True

    return False


async def mostrar_ayuda(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra la guía de ayuda interactiva y comandos usando Rich Message."""
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    is_staff = await check_is_admin_or_staff(uid, update.effective_user)
    user_name = update.effective_user.first_name or "Lector"

    blocks = build_help_rich_blocks(user_rank=user_name, is_staff=is_staff)

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
            logger.debug(f"[mostrar_ayuda] No se pudo editar in-place: {e}")

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )


async def mostrar_donaciones(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra la información de membresías VIP, donaciones y beneficios en Rich Message."""
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    user_name = update.effective_user.first_name or "Lector"
    donation_url = getattr(config, "DONATION_URL", "https://ko-fi.com/zeepubs")

    blocks = build_donations_rich_blocks(
        user_name=user_name,
        donation_url=donation_url,
    )

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
            logger.debug(f"[mostrar_donaciones] No se pudo editar in-place: {e}")

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )


async def mostrar_reglas(
    update: Update, context: ContextTypes.DEFAULT_TYPE, force_new: bool = False
):
    """Muestra las reglas de convivencia y uso responsable de la comunidad."""
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)

    blocks = build_rules_rich_blocks()

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
            logger.debug(f"[mostrar_reglas] No se pudo editar in-place: {e}")

    await RichMessageService.send_rich_message(
        chat_id=chat_id,
        blocks=blocks,
        message_thread_id=thread_id,
    )
