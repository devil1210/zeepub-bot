import asyncio
import io
import logging
import os
import subprocess
from datetime import datetime
from typing import Any

from api.handlers.helpers import check_staff

logger = logging.getLogger(__name__)


async def handle_admin_restart_docker(data: dict[str, Any], user_data: dict[str, Any]):
    """Restart Docker container (admin only)."""
    check_staff(user_data)
    try:
        container_name = os.getenv("CONTAINER_NAME", "zeepub-bot")

        async def do_restart():
            try:
                await asyncio.to_thread(
                    subprocess.run, ["docker", "restart", container_name], timeout=30
                )
            except Exception as e:
                logger.error(f"Error in background docker restart: {e}")

        asyncio.create_task(do_restart())
        return {
            "success": True,
            "message": f"Contenedor {container_name} reiniciándose...",
            "restarting": True,
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


async def handle_admin_update_system(data: dict[str, Any], user_data: dict[str, Any]):
    """Trigger system update (git pull + restart) using existing bot infrastructure."""
    check_staff(user_data)
    try:
        from services.maintenance_service import trigger_watchtower_update

        asyncio.create_task(trigger_watchtower_update())
        return {
            "success": True,
            "message": "Actualización solicitada. El bot contactará con Watchtower.",
            "restarting": True,
        }
    except Exception as e:
        logger.error(f"Error en handle_admin_update_system: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_sync_status(data: dict[str, Any], user_data: dict[str, Any]):
    """Obtiene estado del motor de sincronización optimizado."""
    check_staff(user_data)
    from core.optimized_sync_engine import optimized_sync_engine
    from services.cache_service import cache_manager

    try:
        sync_status = await optimized_sync_engine.get_sync_status()
        cache_stats = await cache_manager.get_stats()
        return {"success": True, "sync_status": sync_status, "cache_stats": cache_stats}
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_force_sync(data: dict[str, Any], user_data: dict[str, Any]):
    """Fuerza sincronización completa de todas las tablas."""
    check_staff(user_data)
    from core.optimized_sync_engine import optimized_sync_engine

    try:
        await optimized_sync_engine.force_sync_all()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error forcing sync: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_get_system_logs(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    from utils.log_manager import log_buffer_handler

    logs = log_buffer_handler.get_logs(
        level=data.get("level", "INFO"), last_hours=data.get("hours")
    )
    return {"success": True, "logs": logs}


async def handle_admin_send_logs_telegram(
    data: dict[str, Any], user_data: dict[str, Any]
):
    check_staff(user_data)
    try:
        from api.main import bot as bot_instance
        from utils.log_manager import log_buffer_handler

        level = data.get("level", "DEBUG")
        hours = data.get("hours")
        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        if not logs:
            return {"success": False, "message": "No hay logs disponibles."}
        log_text = "\n".join(
            [f"[{log['time']}] {log['level']}: {log['msg']}" for log in logs]
        )
        file_obj = io.BytesIO(log_text.encode("utf-8"))
        first_t = logs[0]["timestamp"] if logs else datetime.now().timestamp()
        last_t = logs[-1]["timestamp"] if logs else datetime.now().timestamp()

        def fmt(t):
            return datetime.fromtimestamp(t).strftime("%Y%m%d_%H%M")

        file_obj.name = f"logs_{fmt(first_t)}_{fmt(last_t)}.txt"
        await bot_instance.app.bot.send_document(
            chat_id=user_data.get("user_id"),
            document=file_obj,
            caption=f"📄 Logs del Sistema\nPeriodo: {fmt(first_t)} a {fmt(last_t)}",
            parse_mode="HTML",
        )
        return {"success": True, "message": "Logs enviados correctamente."}
    except Exception as e:
        logger.error(f"Error sending logs to Telegram: {e}")
        return {"success": False, "message": f"Error: {e!s}"}


async def handle_admin_sync_facebook_publications(
    data: dict[str, Any], user_data: dict[str, Any]
):
    """Sincroniza manualmente las publicaciones de Facebook con la base de datos (Staff/Admin)."""
    check_staff(user_data)
    from services.facebook_sync_service import FacebookSyncService

    limit_posts = data.get("limit", 50)
    fetch_all = data.get("fetch_all", False)

    try:
        res = await FacebookSyncService.sync_recent_publications(
            limit_posts=limit_posts, fetch_all=fetch_all
        )
        return res
    except Exception as e:
        logger.error(f"Error en handle_admin_sync_facebook_publications: {e}")
        return {"success": False, "message": str(e)}


async def handle_admin_update_publication_caption(
    data: dict[str, Any], user_data: dict[str, Any]
):
    """Actualiza el caption de una publicación en Facebook o Telegram y en PostgreSQL (Staff/Admin)."""
    check_staff(user_data)
    publication_id = data.get("publication_id")
    new_caption = data.get("new_caption")

    if not publication_id or new_caption is None:
        return {
            "success": False,
            "message": "Parámetros 'publication_id' y 'new_caption' requeridos.",
        }

    from sqlalchemy import select

    from core.db_manager_pg import pg_manager
    from models.communications import BookPublication

    async with pg_manager.get_session() as session:
        stmt = select(BookPublication).where(BookPublication.id == int(publication_id))
        pub = (await session.execute(stmt)).scalar_one_or_none()

        if not pub:
            return {
                "success": False,
                "message": f"Publicación {publication_id} no encontrada.",
            }

        platform = (pub.platform or "").lower()
        update_ok = False

        if "facebook" in platform:
            from services.publisher.facebook_provider import FacebookPublisherProvider

            fb_provider = FacebookPublisherProvider()
            update_ok = await fb_provider.update_post_message(
                post_id=pub.post_id,
                new_message=new_caption,
                target_id=pub.channel_id,
            )
            if not update_ok:
                return {
                    "success": False,
                    "message": "Facebook Graph API no pudo actualizar el post. Verifica que el token de página tenga permisos sobre este post.",
                }

        elif "telegram" in platform:
            from services.publisher.telegram_provider import TelegramPublisherProvider

            tg_provider = TelegramPublisherProvider()
            chat_id = pub.channel_id
            msg_id = None
            if "_" in str(pub.post_id):
                parts = str(pub.post_id).split("_")
                chat_id = parts[0]
                msg_id = parts[1]
            else:
                msg_id = pub.post_id

            if chat_id and msg_id:
                update_ok = await tg_provider.update_post_message(
                    chat_id=chat_id,
                    message_id=int(msg_id),
                    new_message=new_caption,
                )
                if not update_ok:
                    return {
                        "success": False,
                        "message": "Telegram Bot API no pudo actualizar el mensaje en el canal.",
                    }
            else:
                update_ok = True
        else:
            update_ok = True

        # Actualizar en la base de datos local
        pub.caption = new_caption
        await session.commit()

        logger.info(
            f"✅ Publicación {pub.id} ({pub.platform}) actualizada exitosamente por staff {user_data.get('user_id')}."
        )
        return {
            "success": True,
            "publication_id": pub.id,
            "new_caption": new_caption,
            "message": f"Publicación en {pub.platform.capitalize()} actualizada con éxito.",
        }
