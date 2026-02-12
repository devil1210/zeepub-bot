import asyncio
import logging
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from api.handlers.helpers import check_admin, check_staff
from models.publication_models import PublicationChannel, PublicationTemplate
from repositories.publication_repository import pub_repo
from services.publisher.publisher_service import publisher_service

logger = logging.getLogger(__name__)


async def handle_pub_get_queue(data: dict[str, Any], user_data: dict[str, Any]):
    logger.info(f"handle_pub_get_queue called by user {user_data.get('user_id')}")
    check_staff(user_data)

    status = data.get("status")
    limit = data.get("limit", 50)
    items = await pub_repo.get_full_queue(status=status, limit=limit)
    logger.info(f"Found {len(items)} items in publication queue")
    return {
        "items": [
            {
                "id": i.id,
                "book_hash": i.book_hash,
                "channel": i.channel.name if i.channel else "Unknown",
                "channel_id": i.channel_id,
                "template_id": i.template_id,
                "platform": i.channel.platform if i.channel else "Unknown",
                "scheduled_for": i.scheduled_for.isoformat(),
                "status": i.status,
                "published_at": i.published_at.isoformat() if i.published_at else None,
                "error": i.error_message,
                "payload": i.payload,
            }
            for i in items
        ]
    }


async def handle_pub_get_channels(data: dict[str, Any], user_data: dict[str, Any]):
    logger.info(f"handle_pub_get_channels called by user {user_data.get('user_id')}")
    check_staff(user_data)

    # Obtener canales y chats descubiertos
    result = await publisher_service.get_channels_with_discovery(active_only=False)
    logger.info(
        f"Found {len(result.get('channels', []))} channels "
        f"and {len(result.get('discovered', []))} discovered chats"
    )

    return result


async def handle_pub_save_channel(data: dict[str, Any], user_data: dict[str, Any]):
    check_admin(user_data)

    channel_id = data.get("id")
    channel_data = {
        "name": data["name"],
        "platform": data["platform"],
        "target_id": data["target_id"],
        "is_active": data.get("is_active", True),
        "is_favorite": data.get("is_favorite", False),
        "config": data.get("config", {}),
    }

    if channel_id:
        await pub_repo.update_channel(channel_id, channel_data)
    else:
        channel = PublicationChannel(**channel_data)
        await pub_repo.create_channel(channel)
    return {"success": True}


async def handle_pub_toggle_favorite(data: dict[str, Any], user_data: dict[str, Any]):
    """Alterna el estado favorito de un canal."""
    check_admin(user_data)

    channel_id = data.get("id")
    if not channel_id:
        raise HTTPException(status_code=400, detail="Missing id")

    success = await publisher_service.toggle_favorite(int(channel_id))
    return {"success": success}


async def handle_pub_promote_discovered(data: dict[str, Any], user_data: dict[str, Any]):
    """Promueve un chat descubierto a canal oficial."""
    check_admin(user_data)

    chat_id = data.get("chat_id")
    name = data.get("name")

    if not chat_id or not name:
        raise HTTPException(status_code=400, detail="Missing params")

    result = await publisher_service.promote_discovered_to_channel(str(chat_id), name)
    if not result:
        return {"success": False, "message": "Canal ya existe o error"}

    return {"success": True}


async def handle_pub_delete_channel(data: dict[str, Any], user_data: dict[str, Any]):
    check_admin(user_data)

    channel_id = data.get("id")
    if not channel_id:
        raise HTTPException(status_code=400, detail="Falta id")
    await pub_repo.delete_channel(channel_id)
    return {"success": True}


async def handle_pub_get_templates(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    templates = await pub_repo.get_templates(platform=data.get("platform"))
    return {
        "templates": [
            {"id": t.id, "name": t.name, "content": t.content, "platform": t.platform}
            for t in templates
        ]
    }


async def handle_pub_save_template(data: dict[str, Any], user_data: dict[str, Any]):
    check_admin(user_data)

    template_id = data.get("id")
    template_data = {
        "name": data["name"],
        "content": data["content"],
        "platform": data["platform"],
    }

    if template_id:
        await pub_repo.update_template(template_id, template_data)
    else:
        template = PublicationTemplate(**template_data)
        await pub_repo.create_template(template)
    return {"success": True}


async def handle_pub_delete_template(data: dict[str, Any], user_data: dict[str, Any]):
    check_admin(user_data)

    template_id = data.get("id")
    if not template_id:
        raise HTTPException(status_code=400, detail="Falta id")
    await pub_repo.delete_template(template_id)
    return {"success": True}


async def handle_pub_schedule(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    book_hash = data["book_hash"]
    channel_id = data["channel_id"]
    scheduled_for_str = data["scheduled_for"]
    template_id = data.get("template_id")
    payload = data.get("payload")

    # Parse ISO date and convert to naive UTC (SQLAlchemy DateTime default)
    try:
        # First ensure we handle 'Z' or other offsets to get a consistent UTC time
        # Then strip the timezone info to make it naive for the DB column
        dt_aware = datetime.fromisoformat(scheduled_for_str.replace("Z", "+00:00"))
        scheduled_for = dt_aware.replace(tzinfo=None)
    except Exception as e:
        logger.error(f"Error parsing date {scheduled_for_str}: {e}")
        raise HTTPException(status_code=400, detail="Formato de fecha inválido") from e

    await publisher_service.schedule_publication(
        book_hash=book_hash,
        channel_id=channel_id,
        scheduled_for=scheduled_for,
        template_id=template_id,
        payload=payload,
    )

    # Si se pide inmediato, procesar la cola ahora mismo
    if data.get("immediate"):
        logger.info(f"Opcion inmediata detectada para publicación de {book_hash}")
        asyncio.create_task(publisher_service.process_queue())

    return {"success": True}


async def handle_pub_update_queue_item(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    item_id = data.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail="Falta id")

    item = await pub_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    if "scheduled_for" in data:
        try:
            scheduled_for_str = data["scheduled_for"]
            # Parse ISO date
            dt_aware = datetime.fromisoformat(scheduled_for_str.replace("Z", "+00:00"))
            item.scheduled_for = dt_aware.replace(tzinfo=None)
        except Exception as e:
            logger.error(f"Error parsing date: {e}")
            pass

    if "status" in data:
        item.status = data["status"]

    if "payload" in data:
        item.payload = data["payload"]

    if "template_id" in data:
        item.template_id = data["template_id"]

    await pub_repo.update(item)

    return {"success": True}


async def handle_pub_delete_queue_item(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    item_id = data.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail="Falta id")
    await pub_repo.delete(item_id)
    return {"success": True}
