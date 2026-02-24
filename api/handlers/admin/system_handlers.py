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
                await asyncio.to_thread(subprocess.run, ["docker", "restart", container_name], timeout=30)
            except Exception as e:
                logger.error(f"Error in background docker restart: {e}")

        asyncio.create_task(do_restart())
        return {"success": True, "message": f"Contenedor {container_name} reiniciándose...", "restarting": True}
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

    logs = log_buffer_handler.get_logs(level=data.get("level", "INFO"), last_hours=data.get("hours"))
    return {"success": True, "logs": logs}


async def handle_admin_send_logs_telegram(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)
    try:
        from api.main import bot as bot_instance
        from utils.log_manager import log_buffer_handler

        level = data.get("level", "DEBUG")
        hours = data.get("hours")
        logs = log_buffer_handler.get_logs(level=level, last_hours=hours)
        if not logs:
            return {"success": False, "message": "No hay logs disponibles."}
        log_text = "\n".join([f"[{log['time']}] {log['level']}: {log['msg']}" for log in logs])
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
        return {"success": False, "message": f"Error: {str(e)}"}
