import asyncio
import logging
import os
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from api.handlers.helpers import check_admin, check_staff
from models.communications import PublicationChannel, PublicationTemplate
from repositories.publication_repository import pub_repo
from services.publisher.publisher_service import (
    TelegramPublisherProvider,
    publisher_service,
)

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
        from models.library import LocalBook

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
                    "series_spanish": (
                        b.series_info.series_spanish if b.series_info else b.series_spanish or b.title
                    ),
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
                "scheduled_for": (i.scheduled_for.isoformat() + "Z") if i.scheduled_for else None,
                "status": i.status,
                "published_at": (i.published_at.isoformat() + "Z") if i.published_at else None,
                "error": i.error_message,
                "payload": i.payload,
                "series": book_info_map.get(i.book_hash, {}).get("series"),
                "series_spanish": book_info_map.get(i.book_hash, {}).get("series_spanish"),
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
                "is_default": bool(t.is_default),
                "extra_config": t.extra_config or {},
            }
            for t in templates
        ]
    }


async def handle_pub_save_template(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    template_id = data.get("id")
    platform = data.get("platform", "telegram")
    is_default = bool(data.get("is_default", False)) if "is_default" in data else None

    # Si se marca como default, desmarcar las otras plantillas de esa misma plataforma
    if is_default:
        from sqlalchemy import update

        from core.db_manager_pg import pg_manager
        async with pg_manager.get_session() as session:
            await session.execute(
                update(PublicationTemplate)
                .where(PublicationTemplate.platform == platform)
                .values(is_default=False)
            )
            await session.commit()

    template_data = {
        "name": data["name"],
        "content": data["content"],
        "platform": platform,
        "extra_config": data.get("extra_config", {}),
    }
    if is_default is not None:
        template_data["is_default"] = is_default

    if template_id:
        existing = await pub_repo.get_template_by_id(template_id)
        if existing:
            merged_config = (existing.extra_config or {}).copy()
            merged_config.update(data.get("extra_config", {}))
            template_data["extra_config"] = merged_config
            if is_default is None:
                template_data["is_default"] = existing.is_default
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
        dt_aware = datetime.fromisoformat(scheduled_for_str.replace("Z", "+00:00"))
        if dt_aware.tzinfo is not None:
            from datetime import timezone
            scheduled_for = dt_aware.astimezone(timezone.utc).replace(tzinfo=None)
        else:
            scheduled_for = dt_aware
    except Exception as e:
        logger.error(f"Error parsing date {scheduled_for_str}: {e}")
        raise HTTPException(status_code=400, detail="Formato de fecha inválido") from e

    payload = data.get("payload") or {}
    if data.get("fb_album_id"):
        payload["fb_album_id"] = data["fb_album_id"]

    if not template_ids:
        new_q_item = await publisher_service.schedule_publication(
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
            new_q_item = await publisher_service.schedule_publication(
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

    from core.db_manager_pg import pg_manager
    async with pg_manager.get_session() as session:
        pub_repo.session = session
        try:
            item = await pub_repo.get_by_id(int(item_id))
            if not item:
                raise HTTPException(status_code=404, detail="Item no encontrado")

            if "scheduled_for" in data:
                try:
                    scheduled_for_str = data["scheduled_for"]
                    # Parse ISO date
                    dt_aware = datetime.fromisoformat(scheduled_for_str.replace("Z", "+00:00"))
                    if dt_aware.tzinfo is not None:
                        from datetime import timezone
                        item.scheduled_for = dt_aware.astimezone(timezone.utc).replace(tzinfo=None)
                    else:
                        item.scheduled_for = dt_aware
                except Exception as e:
                    logger.error(f"Error parsing date: {e}")

            if "status" in data:
                item.status = data["status"]

            if "payload" in data:
                item.payload = data["payload"]

            if "fb_album_id" in data:
                current_payload = dict(item.payload) if isinstance(item.payload, dict) else {}
                current_payload["fb_album_id"] = data["fb_album_id"]
                item.payload = current_payload

            if "template_id" in data:
                item.template_id = int(data["template_id"]) if data["template_id"] else None

            await session.commit()
        finally:
            pub_repo.session = None

    return {"success": True}


async def handle_pub_delete_queue_item(data: dict[str, Any], user_data: dict[str, Any]):
    check_staff(user_data)

    item_id = data.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail="Falta id")
    
    from core.db_manager_pg import pg_manager
    async with pg_manager.get_session() as session:
        pub_repo.session = session
        try:
            await pub_repo.delete(int(item_id))
            await session.commit()
        finally:
            pub_repo.session = None

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


async def handle_pub_update_post(data: dict[str, Any], user_data: dict[str, Any]):
    """
    Paso 2: Actualiza la publicación existente de un libro (en Facebook u otras redes)
    sin crear un post duplicado.
    """
    check_staff(user_data)
    book_id = data.get("book_id") or data.get("book_hash") or data.get("id")
    if not book_id:
        raise HTTPException(status_code=400, detail="Missing book_id")

    new_caption = data.get("caption")
    template_id = data.get("template_id")
    platforms = data.get("platforms") or ["telegram", "facebook"]

    result = await publisher_service.update_published_book(
        book_hash=str(book_id),
        new_caption=new_caption,
        template_id=int(template_id) if template_id else None,
        platforms=platforms,
    )

    if not result.get("success"):
        error_msg = (
            result.get("error")
            or result.get("telegram_note")
            or result.get("facebook_note")
            or "No se pudo actualizar la publicación"
        )
        return {"success": False, "error": error_msg, "result": result}

    return {"success": True, "result": result}


async def handle_pub_check_facebook_album(data: dict[str, Any], user_data: dict[str, Any]):
    """
    Verifica si el álbum de Facebook para la serie de un libro existe en la página de destino.
    Retorna el estado de existencia y el nombre exacto recomendado para crearlo si falta.
    """
    check_staff(user_data)
    book_id = data.get("book_id") or data.get("book_hash") or data.get("id")
    if not book_id:
        raise HTTPException(status_code=400, detail="Missing book_id")

    channel_id = data.get("channel_id")

    result = await publisher_service.check_facebook_album(
        book_hash=str(book_id),
        channel_id=int(channel_id) if channel_id else None,
    )

    return {"success": True, **result}


async def handle_pub_send_template_to_chat(data: dict[str, Any], user_data: dict[str, Any]):
    """
    Envía la plantilla de publicación de Facebook (resuelta con los datos del libro)
    al chat privado de Telegram del admin/staff, envuelta en un Rich Message con <blockquote>
    o <code> para copiar directamente.
    """
    check_staff(user_data)

    target_chat_id = user_data.get("telegram_id") or user_data.get("user_id")
    if not target_chat_id:
        raise HTTPException(status_code=400, detail="No se identificó tu ID de Telegram")

    book_id = data.get("book_id") or data.get("book_hash") or data.get("id")
    if not book_id:
        raise HTTPException(status_code=400, detail="Falta book_id")

    # 1. Obtener libro y resolver metadatos
    from sqlalchemy import or_, select
    from sqlalchemy.orm import selectinload

    from core.db_manager_pg import pg_manager
    from models.library import LocalBook
    from services.workgroup_service import workgroup_service
    from utils.helpers import clean_caption_for_facebook, escape_html
    from utils.template_engine import apply_publication_template

    async with pg_manager.get_session() as session:
        stmt = (
            select(LocalBook)
            .options(selectinload(LocalBook.series_info))
            .where(
                or_(
                    LocalBook.id == str(book_id),
                    LocalBook.short_link == str(book_id),
                    LocalBook.book_hash == str(book_id),
                )
            )
        )
        book = (await session.execute(stmt)).scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        book_data = publisher_service._build_book_data_dict(book)
        credits_meta = await workgroup_service.resolve_book_workgroup_credits(
            book_id=book.id,
            book_obj=book,
            raw_meta=book_data,
            public_link=book_data.get("download_link"),
        )
        book_data.update(credits_meta)

        # 2. Obtener plantilla de Facebook (la default o la primera activa)
        template_id = data.get("template_id")
        raw_caption = ""
        if template_id:
            tpl = await pub_repo.get_template_by_id(int(template_id))
            if tpl and tpl.content:
                raw_caption = apply_publication_template(tpl.content, book_data)

        if not raw_caption:
            fb_templates = await pub_repo.get_templates(platform="facebook")
            def_tpl = next((t for t in fb_templates if t.is_default), None) or (fb_templates[0] if fb_templates else None)
            if def_tpl and def_tpl.content:
                raw_caption = apply_publication_template(def_tpl.content, book_data)

        if not raw_caption:
            raw_caption = apply_publication_template(
                TelegramPublisherProvider.FB_CAPTION_TEMPLATE, book_data
            )

        final_facebook_text = clean_caption_for_facebook(raw_caption)

    # 3. Preparar portada si existe
    cover_source = (
        book_data.get("cover_high")
        or book_data.get("cover_original")
        or book_data.get("portada")
    )
    from services.cover_service import resolve_cover_data
    resolved_cover = await resolve_cover_data(cover_source) if cover_source else None

    files = None
    media = None
    if resolved_cover:
        if isinstance(resolved_cover, bytes):
            files = {"fb_cover": ("cover.jpg", resolved_cover, "image/jpeg")}
        elif isinstance(resolved_cover, str) and os.path.exists(resolved_cover):
            try:
                with open(resolved_cover, "rb") as f:
                    files = {"fb_cover": ("cover.jpg", f.read(), "image/jpeg")}
            except Exception as e:
                logger.warning(f"Error al leer portada local para preview de plantilla: {e}")

        if files:
            media = [
                {
                    "id": "fb_cover",
                    "media": {
                        "type": "photo",
                        "media": "attach://fb_cover",
                    },
                }
            ]

    # 4. Construir Rich Message con portada y el texto envuelto en bloque de código copiador
    titulo_libro = book_data.get("spanish_title") or book_data.get("title") or "Libro"
    vol_libro = f" - Vol. {book_data.get('volume')}" if book_data.get("volume") is not None else ""

    html_parts = []
    if media:
        html_parts.append('<img src="tg://photo?id=fb_cover" />\n')

    html_parts.append("<h3>📋 Plantilla de Publicación para Facebook</h3>")
    html_parts.append(f"<p><b>📖 {escape_html(str(titulo_libro))}{vol_libro}</b></p>")
    html_parts.append("<p><i>Toca el recuadro de abajo para copiar el texto con todos sus saltos de línea:</i></p>")
    html_parts.append(f"<pre><code class=\"language-copy\">{escape_html(final_facebook_text)}</code></pre>")

    html_content = "\n".join(html_parts)

    # 5. Enviar vía RichMessageService
    from services.rich_message_service import RichMessageService
    rich_sent = False
    try:
        res = await RichMessageService.send_rich_message(
            chat_id=target_chat_id,
            html=html_content,
            media=media,
            files=files if files else None,
        )
        if res and res.get("ok"):
            rich_sent = True
    except Exception as e:
        logger.warning(f"Error enviando Rich Message con plantilla a {target_chat_id}: {e}")

    # Fallback tradicional si falla
    if not rich_sent:
        fallback_msg = (
            f"📋 <b>Plantilla de Publicación (Facebook)</b>\n"
            f"<b>{escape_html(str(titulo_libro))}{vol_libro}</b>\n\n"
            f"<pre><code class=\"language-copy\">{escape_html(final_facebook_text)}</code></pre>"
        )
        try:
            from api.main import bot as main_bot
            from services.cover_service import send_photo_bytes
            tg_bot = main_bot.app.bot

            if resolved_cover:
                await send_photo_bytes(
                    tg_bot, target_chat_id, fallback_msg, resolved_cover, parse_mode="HTML"
                )
            else:
                await tg_bot.send_message(
                    chat_id=target_chat_id, text=fallback_msg, parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Error en fallback de envío de plantilla a Telegram: {e}")
            raise HTTPException(status_code=500, detail=f"No se pudo enviar la plantilla a Telegram: {e}")

    return {"success": True, "message": "Plantilla enviada exitosamente a tu chat de Telegram"}


async def handle_pub_create_draft(data: dict[str, Any], user_data: dict[str, Any]) -> dict[str, Any]:
    """Crea un borrador (DRAFT) directamente en Meta Business Suite / Facebook para el libro."""
    book_id = data.get("book_id") or data.get("book_hash") or data.get("id")
    if not book_id:
        raise HTTPException(status_code=400, detail="Falta book_id")

    from sqlalchemy import or_, select
    from sqlalchemy.orm import selectinload

    from core.db_manager_pg import pg_manager
    from models.library import LocalBook
    from services.workgroup_service import workgroup_service
    from utils.helpers import clean_caption_for_facebook
    from utils.template_engine import apply_publication_template

    async with pg_manager.get_session() as session:
        stmt = (
            select(LocalBook)
            .options(selectinload(LocalBook.series_info))
            .where(
                or_(
                    LocalBook.id == str(book_id),
                    LocalBook.short_link == str(book_id),
                    LocalBook.book_hash == str(book_id),
                )
            )
        )
        book = (await session.execute(stmt)).scalar_one_or_none()
        if not book:
            raise HTTPException(status_code=404, detail="Libro no encontrado")

        book_data = publisher_service._build_book_data_dict(book)
        credits_meta = await workgroup_service.resolve_book_workgroup_credits(
            book_id=book.id,
            book_obj=book,
            raw_meta=book_data,
            public_link=book_data.get("download_link"),
        )
        book_data.update(credits_meta)

        # Obtener canal de Facebook
        fb_channels = await pub_repo.get_channels(platform="facebook")
        if not fb_channels:
            raise HTTPException(status_code=400, detail="No tienes ningún canal de Facebook configurado")
        target_channel = fb_channels[0]

        # Obtener plantilla de Facebook
        template_id = data.get("template_id")
        raw_caption = ""
        if template_id:
            tpl = await pub_repo.get_template_by_id(int(template_id))
            if tpl and tpl.content:
                raw_caption = apply_publication_template(tpl.content, book_data)

        if not raw_caption:
            fb_templates = await pub_repo.get_templates(platform="facebook")
            def_tpl = next((t for t in fb_templates if t.is_default), None) or (fb_templates[0] if fb_templates else None)
            if def_tpl and def_tpl.content:
                raw_caption = apply_publication_template(def_tpl.content, book_data)

        if not raw_caption:
            raw_caption = apply_publication_template(
                TelegramPublisherProvider.FB_CAPTION_TEMPLATE, book_data
            )

        final_facebook_text = clean_caption_for_facebook(raw_caption)

    # Disparar creación de borrador en Facebook Provider
    fb_provider = publisher_service.providers.get("facebook")
    if not fb_provider:
        raise HTTPException(status_code=500, detail="Proveedor de Facebook no disponible")

    success = await fb_provider.announce_book(
        target_channel.target_id,
        book_data,
        options={
            "caption": final_facebook_text,
            "page_access_token": target_channel.config.get("page_access_token") if target_channel.config else None,
            "is_draft": True,
        },
    )

    if not success:
        raise HTTPException(status_code=500, detail="Error al crear el borrador en Meta Business Suite")

    return {"success": True, "message": "¡Borrador creado con éxito en Meta Business Suite!"}


