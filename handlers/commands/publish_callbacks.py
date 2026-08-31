# handlers/commands/publish_callbacks.py
"""
Manejador especializado de publicación y programación en canales de Telegram.
"""

import logging
from datetime import datetime, timedelta, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config.config_settings import config
from core.state_manager import state_manager
from services.keyboard_factory import BotKeyboards
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


async def handle_publish_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> bool:
    """Procesa callbacks de publicación y programación en canales. Retorna True si fue manejado."""
    query = update.callback_query
    if not query:
        return False

    uid = update.effective_user.id
    st = state_manager.get_user_state(uid)

    if data.startswith("pub_menu|"):
        key = data.split("|")[1]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Información del libro no encontrada.", show_alert=True)
            return True
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
        return True

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
        return True

    elif data.startswith("pub_now|"):
        key = data.split("|")[1]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Libro no encontrado.", show_alert=True)
            return True
        book_hash = libro_st.get("hash")
        await query.answer("🚀 Procesando publicación inmediata...", show_alert=False)

        try:
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
        return True

    elif data.startswith("pub_in|") or data.startswith("pub_preset|"):
        parts = data.split("|")
        key = parts[2]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Libro no encontrado.", show_alert=True)
            return True
        book_hash = libro_st.get("hash")

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
        return True

    return False
