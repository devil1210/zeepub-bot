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

    # Enrichment: Pre-fetch book info for the whole queue
    book_hashes = {i.book_hash for i in items}
    book_info_map = {}
    if book_hashes:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from core.db_manager_pg import pg_manager
        from models.library_models import LocalBook

        async with pg_manager.get_session() as session:
            stmt = (
                select(LocalBook)
                .options(selectinload(LocalBook.series_info))
                .where(LocalBook.book_hash.in_(list(book_hashes)))
            )
            result = await session.execute(stmt)
            for b in result.scalars():
                book_info_map[b.book_hash] = {
                    "series": (b.series_info.series_name if b.series_info else b.title),
                    "volume": b.volume,
                }

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
                "series": book_info_map.get(i.book_hash, {}).get("series"),
                "volume": book_info_map.get(i.book_hash, {}).get("volume"),
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
        f"Found {len(result.get('channels', []))} channels and {len(result.get('discovered', []))} discovered chats"
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

    # Seed default templates if none exist for Telegram
    has_telegram = any(t.platform == "telegram" for t in templates)
    target_platform = data.get("platform")

    if (not target_platform or target_platform == "telegram") and not has_telegram:
        from services.publisher.publisher_service import TelegramPublisherProvider

        defaults = [
            PublicationTemplate(
                name="Default Telegram Cover",
                content=TelegramPublisherProvider.COVER_TEMPLATE,
                platform="telegram",
                extra_config={"type": "cover"},
            ),
            PublicationTemplate(
                name="Default Telegram Synopsis",
                content=TelegramPublisherProvider.SYNOPSIS_TEMPLATE,
                platform="telegram",
                extra_config={"type": "synopsis"},
            ),
            PublicationTemplate(
                name="Default Telegram Info",
                content=TelegramPublisherProvider.INFO_TEMPLATE,
                platform="telegram",
                extra_config={"type": "info"},
            ),
            PublicationTemplate(
                name="Default Telegram Unified",
                content=TelegramPublisherProvider.FULL_TEMPLATE,
                platform="telegram",
                is_default=True,
                extra_config={"type": "unified"},
            ),
        ]

        for t in defaults:
            created = await pub_repo.create_template(t)
            templates.append(created)

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "content": t.content,
                "platform": t.platform,
                "extra_config": t.extra_config or {},
            }
            for t in templates
        ]
    }


async def handle_pub_save_template(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    template_id = data.get("id")
    template_data = {
        "name": data["name"],
        "content": data["content"],
        "platform": data["platform"],
        "extra_config": data.get("extra_config", {}),
    }

    if template_id:
        await pub_repo.update_template(template_id, template_data)
    else:
        template = PublicationTemplate(**template_data)
        await pub_repo.create_template(template)
    return {"success": True}


async def handle_pub_delete_template(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    template_id = data.get("id")
    if not template_id:
        raise HTTPException(status_code=400, detail="Falta id")
    await pub_repo.delete_template(template_id)
    return {"success": True}


async def handle_pub_restore_templates(data: dict[str, Any], user_data: dict[str, Any]):
    """Restaura las plantillas por defecto de Telegram."""
    check_staff(user_data)

    from services.publisher.publisher_service import TelegramPublisherProvider

    # Definir templates por defecto
    defaults = [
        PublicationTemplate(
            name="Default Telegram Cover",
            content=TelegramPublisherProvider.COVER_TEMPLATE,
            platform="telegram",
            extra_config={"type": "cover"},
        ),
        PublicationTemplate(
            name="Default Telegram Synopsis",
            content=TelegramPublisherProvider.SYNOPSIS_TEMPLATE,
            platform="telegram",
            extra_config={"type": "synopsis"},
        ),
        PublicationTemplate(
            name="Default Telegram Info",
            content=TelegramPublisherProvider.INFO_TEMPLATE,
            platform="telegram",
            extra_config={"type": "info"},
        ),
        PublicationTemplate(
            name="Default Telegram Unified",
            content=TelegramPublisherProvider.FULL_TEMPLATE,
            platform="telegram",
            is_default=True,
            extra_config={"type": "unified"},
        ),
    ]

    # Eliminar templates existentes de Telegram
    existing = await pub_repo.get_templates(platform="telegram")
    for t in existing:
        await pub_repo.delete_template(t.id)

    # Crear los nuevos
    created = []
    for t in defaults:
        created.append(await pub_repo.create_template(t))

    return {
        "success": True,
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "content": t.content,
                "platform": t.platform,
                "extra_config": t.extra_config or {},
            }
            for t in created
        ],
    }


async def handle_pub_schedule(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    book_hash = data["book_hash"]
    channel_id = data["channel_id"]
    scheduled_for_str = data["scheduled_for"]
    template_id = data.get("template_id")
    template_ids = data.get("template_ids", [])
    payload = data.get("payload")

    if template_id and template_id not in template_ids:
        template_ids = [template_id] + template_ids

    # Parse ISO date and convert to naive UTC (SQLAlchemy DateTime default)
    try:
        # First ensure we handle 'Z' or other offsets to get a consistent UTC time
        # Then strip the timezone info to make it naive for the DB column
        dt_aware = datetime.fromisoformat(scheduled_for_str.replace("Z", "+00:00"))
        scheduled_for = dt_aware.replace(tzinfo=None)
    except Exception as e:
        logger.error(f"Error parsing date {scheduled_for_str}: {e}")
        raise HTTPException(status_code=400, detail="Formato de fecha inválido") from e

    if not template_ids:
        await publisher_service.schedule_publication(
            book_hash=book_hash,
            channel_id=channel_id,
            scheduled_for=scheduled_for,
            template_id=template_id,
            payload=payload,
        )
    else:
        import datetime as dt

        for i, tid in enumerate(template_ids):
            staggered_time = scheduled_for + dt.timedelta(seconds=2 * i)
            await publisher_service.schedule_publication(
                book_hash=book_hash,
                channel_id=channel_id,
                scheduled_for=staggered_time,
                template_id=tid,
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


async def handle_pub_quick_post(data: dict[str, Any], user_data: dict[str, Any]):
    """Publica un libro inmediatamente a un canal usando el template por defecto."""
    check_staff(user_data)
    book_id = data.get("book_id")
    channel_id = data.get("channel_id")

    if not book_id or not channel_id:
        raise HTTPException(status_code=400, detail="Missing book_id or channel_id")

    # Obtener el canal
    channel = await pub_repo.get_channel_by_id(int(channel_id))
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    # Obtener el template por defecto para la plataforma
    templates = await pub_repo.get_templates(platform=channel.platform)
    template = next((t for t in templates if t.is_default), None)
    if not template and templates:
        template = templates[0]

    # Programar para ahora mismo
    await publisher_service.schedule_publication(
        book_hash=str(book_id),
        channel_id=int(channel_id),
        scheduled_for=datetime.utcnow(),
        template_id=template.id if template else None,
    )

    # Procesar cola inmediatamente en segundo plano
    asyncio.create_task(publisher_service.process_queue())

    return {"success": True}
