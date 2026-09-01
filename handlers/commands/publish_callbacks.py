# handlers/commands/publish_callbacks.py
"""
Manejador especializado de publicación y programación en canales de Telegram con Rich Messages.
"""

import logging
from datetime import datetime, timedelta, timezone

from telegram import Update
from telegram.ext import ContextTypes

from core.state_manager import state_manager
from services.publisher.publisher_service import publisher_service
from services.rich_message_service import RichMessageService
from utils.helpers import get_thread_id

logger = logging.getLogger(__name__)


async def _get_telegram_channels() -> list[dict]:
    """Helper para obtener canales activos de Telegram."""
    try:
        channels_data = await publisher_service.get_channels_with_discovery(active_only=True)
        all_channels = channels_data.get("channels", [])
        return [c for c in all_channels if c.get("platform") == "telegram" and c.get("is_active")]
    except Exception as e:
        logger.error(f"Error obteniendo canales de Telegram: {e}")
        return []


def _get_target_channel(tg_channels: list[dict]) -> dict | None:
    """Selecciona el canal oficial prioritario."""
    if not tg_channels:
        return None
    return (
        next(
            (
                c for c in tg_channels
                if "@zeepubs" in str(c.get("target_id", "")).lower()
                or "oficial" in str(c.get("name", "")).lower()
                or c.get("is_favorite")
            ),
            None,
        )
        or tg_channels[0]
    )


async def handle_publish_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE, data: str
) -> bool:
    """Procesa callbacks de publicación y programación en canales. Retorna True si fue manejado."""
    query = update.callback_query
    if not query:
        return False

    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    thread_id = get_thread_id(update)
    st = state_manager.get_user_state(uid)

    # 1. Menú Principal de Publicación (Inmediata vs Programada)
    if data.startswith("pub_menu|") or data.startswith("pub_channel|"):
        key = data.split("|")[1]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Información del libro no encontrada.", show_alert=True)
            return True

        title = libro_st.get("titulo") or libro_st.get("english_title") or "Novela"
        vol_display = libro_st.get("vol_display") or str(libro_st.get("volume") or "1.0")

        tg_channels = await _get_telegram_channels()
        target_ch = _get_target_channel(tg_channels)
        ch_label = f"{target_ch['name']} ({target_ch['target_id']})" if target_ch else "Canal Oficial (@ZeePubs)"

        blocks = [
            {"type": "heading", "size": 2, "text": "📢 Publicar en Telegram"},
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": [
                    [{"text": "📖 Novela", "align": "left"}, {"text": str(title), "align": "left"}],
                    [{"text": "📦 Volumen", "align": "left"}, {"text": f"Vol. {vol_display}", "align": "left"}],
                    [{"text": "🌐 Canal Destino", "align": "left"}, {"text": str(ch_label), "align": "left"}],
                ],
            },
            {
                "type": "paragraph",
                "text": "<i>Selecciona cómo deseas publicar este volumen en el canal oficial:</i>",
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "⚡ Publicar Ahora", "callback_data": f"pub_now|{key}"},
                ],
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "⏰ Programar Publicación", "callback_data": f"pub_sched_menu|{key}"},
                ],
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "⬅️ Volver a la Serie", "callback_data": f"sel_vol|{key}"},
                    {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                    {"text": "❌ Salir", "callback_data": "salir"},
                ],
            },
        ]

        await RichMessageService.edit_rich_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            blocks=blocks,
        )
        return True

    # 2. Menú de Programación Horaria
    elif data.startswith("pub_sched_menu|"):
        key = data.split("|")[1]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Información del libro no encontrada.", show_alert=True)
            return True

        title = libro_st.get("titulo") or libro_st.get("english_title") or "Novela"
        vol_display = libro_st.get("vol_display") or str(libro_st.get("volume") or "1.0")

        blocks = [
            {"type": "heading", "size": 2, "text": "⏰ Programar Publicación"},
            {
                "type": "table",
                "is_bordered": True,
                "is_striped": True,
                "is_compact": True,
                "cells": [
                    [{"text": "📖 Novela", "align": "left"}, {"text": str(title), "align": "left"}],
                    [{"text": "📦 Volumen", "align": "left"}, {"text": f"Vol. {vol_display}", "align": "left"}],
                ],
            },
            {
                "type": "paragraph",
                "text": "<i>Selecciona cuándo deseas que el bot publique automáticamente este volumen:</i>",
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "⏱️ En 1 hora", "callback_data": f"pub_in|1|{key}"},
                    {"text": "⏱️ En 2 horas", "callback_data": f"pub_in|2|{key}"},
                    {"text": "⏱️ En 6 horas", "callback_data": f"pub_in|6|{key}"},
                ],
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "🌅 Mañana 10:00 AM", "callback_data": f"pub_preset|tomorrow_10|{key}"},
                    {"text": "🌆 Mañana 18:00 PM", "callback_data": f"pub_preset|tomorrow_18|{key}"},
                ],
            },
            {
                "type": "buttons",
                "align": "center",
                "buttons": [
                    {"text": "⬅️ Volver a Opciones", "callback_data": f"pub_menu|{key}"},
                    {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                    {"text": "❌ Salir", "callback_data": "salir"},
                ],
            },
        ]

        await RichMessageService.edit_rich_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
            blocks=blocks,
        )
        return True

    # 3. Publicación Inmediata
    elif data.startswith("pub_now|"):
        key = data.split("|")[1]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Libro no encontrado.", show_alert=True)
            return True

        title = libro_st.get("titulo") or libro_st.get("english_title") or "Novela"
        vol_display = libro_st.get("vol_display") or str(libro_st.get("volume") or "1.0")
        book_hash = libro_st.get("hash") or libro_st.get("book_hash") or libro_st.get("id")

        await query.answer("🚀 Enviando publicación al canal...", show_alert=False)

        try:
            tg_channels = await _get_telegram_channels()
            target_ch = _get_target_channel(tg_channels)

            if target_ch:
                target_ch_id = target_ch["id"]
                target_name = target_ch.get("name", "Canal Oficial")
                target_handle = target_ch.get("target_id", "@ZeePubs")

                queue_item = await publisher_service.schedule_publication(
                    book_hash=book_hash,
                    channel_id=target_ch_id,
                    scheduled_for=datetime.now(timezone.utc),
                )
                if queue_item and hasattr(queue_item, "id"):
                    await publisher_service.process_queue_item_direct(queue_item.id)
                else:
                    await publisher_service.process_queue()

                blocks = [
                    {"type": "heading", "size": 2, "text": "✅ ¡Publicación Enviada!"},
                    {
                        "type": "table",
                        "is_bordered": True,
                        "is_striped": True,
                        "is_compact": True,
                        "cells": [
                            [{"text": "📖 Novela", "align": "left"}, {"text": str(title), "align": "left"}],
                            [{"text": "📦 Volumen", "align": "left"}, {"text": f"Vol. {vol_display}", "align": "left"}],
                            [{"text": "🌐 Canal Destino", "align": "left"}, {"text": f"{target_name} ({target_handle})", "align": "left"}],
                            [{"text": "📊 Estado", "align": "left"}, {"text": "✅ Publicado en vivo", "align": "left"}],
                        ],
                    },
                    {
                        "type": "paragraph",
                        "text": f"🎉 El volumen ha sido publicado con éxito en <b>{target_handle}</b>.",
                    },
                    {
                        "type": "buttons",
                        "align": "center",
                        "buttons": [
                            {"text": "⬅️ Volver a la Serie", "callback_data": f"sel_vol|{key}"},
                            {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                        ],
                    },
                ]
            else:
                blocks = [
                    {"type": "heading", "size": 2, "text": "⚠️ Sin Canales Configurados"},
                    {
                        "type": "paragraph",
                        "text": "No se encontraron canales de Telegram activos registrados para publicar.",
                    },
                    {
                        "type": "buttons",
                        "align": "center",
                        "buttons": [
                            {"text": "⬅️ Volver al Libro", "callback_data": f"sel_vol|{key}"},
                            {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                        ],
                    },
                ]

            await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=query.message.message_id,
                blocks=blocks,
            )
        except Exception as e:
            logger.error(f"Error publicando en Telegram: {e}", exc_info=True)
            await query.answer(f"❌ Error al publicar: {e}", show_alert=True)
        return True

    # 4. Programación por Preset u Horas
    elif data.startswith("pub_in|") or data.startswith("pub_preset|"):
        parts = data.split("|")
        key = parts[2]
        libro_st = st.get("libros", {}).get(key)
        if not libro_st:
            await query.answer("⚠️ Libro no encontrado.", show_alert=True)
            return True

        title = libro_st.get("titulo") or libro_st.get("english_title") or "Novela"
        vol_display = libro_st.get("vol_display") or str(libro_st.get("volume") or "1.0")
        book_hash = libro_st.get("hash") or libro_st.get("book_hash") or libro_st.get("id")

        now = datetime.now(timezone.utc)
        if parts[0] == "pub_in":
            hours = int(parts[1])
            sched_time = now + timedelta(hours=hours)
            time_desc = f"dentro de {hours} hora(s) ({sched_time.strftime('%H:%M UTC')})"
        else:
            preset = parts[1]
            tomorrow = now + timedelta(days=1)
            if preset == "tomorrow_10":
                sched_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                time_desc = f"mañana a las 10:00 AM UTC ({sched_time.strftime('%d/%m')})"
            else:
                sched_time = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
                time_desc = f"mañana a las 18:00 PM UTC ({sched_time.strftime('%d/%m')})"

        await query.answer("⏰ Programando publicación...", show_alert=False)

        try:
            tg_channels = await _get_telegram_channels()
            target_ch = _get_target_channel(tg_channels)

            if target_ch:
                target_ch_id = target_ch["id"]
                target_name = target_ch.get("name", "Canal Oficial")
                target_handle = target_ch.get("target_id", "@ZeePubs")

                await publisher_service.schedule_publication(
                    book_hash=book_hash,
                    channel_id=target_ch_id,
                    scheduled_for=sched_time,
                )

                blocks = [
                    {"type": "heading", "size": 2, "text": "⏰ ¡Publicación Programada!"},
                    {
                        "type": "table",
                        "is_bordered": True,
                        "is_striped": True,
                        "is_compact": True,
                        "cells": [
                            [{"text": "📖 Novela", "align": "left"}, {"text": str(title), "align": "left"}],
                            [{"text": "📦 Volumen", "align": "left"}, {"text": f"Vol. {vol_display}", "align": "left"}],
                            [{"text": "🌐 Canal", "align": "left"}, {"text": f"{target_name} ({target_handle})", "align": "left"}],
                            [{"text": "📅 Fecha / Hora", "align": "left"}, {"text": time_desc, "align": "left"}],
                            [{"text": "📊 Estado", "align": "left"}, {"text": "⏳ En cola programada", "align": "left"}],
                        ],
                    },
                    {
                        "type": "paragraph",
                        "text": f"🕒 El bot publicará automáticamente esta novela en <b>{target_handle}</b> a la hora programada.",
                    },
                    {
                        "type": "buttons",
                        "align": "center",
                        "buttons": [
                            {"text": "⬅️ Volver a la Serie", "callback_data": f"sel_vol|{key}"},
                            {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                        ],
                    },
                ]
            else:
                blocks = [
                    {"type": "heading", "size": 2, "text": "⚠️ Sin Canales Configurados"},
                    {
                        "type": "paragraph",
                        "text": "No se encontraron canales de Telegram activos registrados para programar.",
                    },
                    {
                        "type": "buttons",
                        "align": "center",
                        "buttons": [
                            {"text": "⬅️ Volver al Libro", "callback_data": f"sel_vol|{key}"},
                            {"text": "🏠 Inicio", "callback_data": "volver_menu"},
                        ],
                    },
                ]

            await RichMessageService.edit_rich_message(
                chat_id=chat_id,
                message_id=query.message.message_id,
                blocks=blocks,
            )
        except Exception as e:
            logger.error(f"Error programando publicación: {e}", exc_info=True)
            await query.answer(f"❌ Error al programar: {e}", show_alert=True)
        return True

    return False
