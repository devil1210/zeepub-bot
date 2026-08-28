import asyncio
import io
import logging
import os
import re
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

# from core.state_manager import state_manager (Moved to local scope)
# from core.session_manager import session_manager (Moved to local scope)
from config.config_settings import config
from utils.download_limiter import can_download, downloads_left
from utils.helpers import normalize_demography
from utils.http_client import cleanup_tmp, fetch_bytes

logger = logging.getLogger(__name__)

# Re-export cover/media functions from dedicated module for backward compatibility
from services.cover_service import (
    resolve_cover_data,
    send_doc_bytes,
    send_photo_bytes,
)


def is_authorized_group(chat_id_or_username: int | str | None) -> bool:
    """
    Verifica si un grupo está explícitamente autorizado por el administrador
    para permitir descargas públicas regulares en lugar de mensajes efímeros.
    Configurable vía setting: 'authorized_download_groups'.
    """
    if not chat_id_or_username:
        return False
    from services.settings_service import get_setting

    raw = get_setting("authorized_download_groups", "")
    if not raw:
        return False

    allowed = [item.strip() for item in str(raw).split(",") if item.strip()]
    str_chat = str(chat_id_or_username).strip()
    return (
        str_chat in allowed
        or (str_chat.startswith("-100") and str_chat[4:] in allowed)
        or (not str_chat.startswith("-100") and f"-100{str_chat}" in allowed)
    )


async def publicar_libro(
    update,
    context: ContextTypes.DEFAULT_TYPE,
    uid: int,
    titulo: str,
    portada_url: str,
    epub_url: str,
    menu_prep: tuple | None = None,
):
    """Descarga EPUB para metadatos, muestra portada, sinopsis y botones."""
    from core.session_manager import session_manager
    from core.state_manager import state_manager
    from services.metadata_orchestrator.metadata_service import metadata_orchestrator
    from services.publisher.publisher_service import publisher_service
    from utils.helpers import get_thread_id

    user_state = state_manager.get_user_state(uid)
    lock = session_manager.get_publish_lock(uid)

    async with lock:
        thread_id_origen = get_thread_id(update)
        destino = user_state.get("destino") or update.effective_chat.id
        chat_origen = user_state.get("chat_origen") or destino
        _ = user_state.get("series_id")  # Reserved for future use
        _ = user_state.get("volume_id")  # Reserved for future use
        user_state["ultima_pagina"] = user_state.get("url", config.BASE_URL)

        # Topic resolution for Catalog
        thread_id_destino = thread_id_origen if destino == chat_origen else None
        if uid == destino:
            from services.topic_service import topic_service

            topic_id = await topic_service.get_topic_id(uid, "catalogo")
            if topic_id:
                thread_id_destino = topic_id

        # 1. Quota Check
        if not await can_download(uid):
            await context.bot.send_message(
                chat_id=destino,
                text="🚫 Has alcanzado tu límite de descargas por hoy.",
                message_thread_id=thread_id_destino,
            )
            return

        # 2. Metadata Gathering and Enrichment
        meta = {}

        epub_downloaded = None
        if epub_url:
            if epub_url.startswith("http://") or epub_url.startswith("https://"):
                epub_downloaded = await fetch_bytes(epub_url, timeout=120)
            else:
                try:
                    import asyncio

                    def read_local():
                        with open(epub_url, "rb") as f:
                            return f.read()

                    epub_downloaded = await asyncio.to_thread(read_local)
                except Exception as e:
                    logger.error(f"Error al leer el archivo local {epub_url}: {e}")

            if epub_downloaded:
                # Use orchestrator for enrichment
                meta = await metadata_orchestrator.get_enriched_metadata(
                    book_id=epub_url, epub_bytes=epub_downloaded
                )

                # Maintain state for subsequent download click
                user_state["epub_buffer"] = epub_downloaded
                user_state["epub_url"] = epub_url
                user_state["meta_pendiente"] = meta

                # Calculate size for display
                if isinstance(epub_downloaded, bytes | bytearray):
                    meta["size_mb"] = len(epub_downloaded) / (1024 * 1024)
                elif isinstance(epub_downloaded, str):
                    meta["size_mb"] = os.path.getsize(epub_downloaded) / (1024 * 1024)

        # Fallback for cover and title
        if not meta.get("cover"):
            meta["cover"] = portada_url
        if not meta.get("title"):
            meta["title"] = titulo

        # 3. Cleanup "Preparing" message
        if menu_prep:
            try:
                await context.bot.delete_message(
                    chat_id=menu_prep[0], message_id=menu_prep[1]
                )
            except Exception:
                pass

        # 4. Announce Book using PublisherService (or skip if direct download)
        user_state["portada_pendiente"] = portada_url
        user_state["titulo_pendiente"] = titulo

        if menu_prep:
            # Es una descarga directa iniciada por el usuario (dl_confirm), saltamos el anuncio
            await descargar_epub_pendiente(update, context, uid)
        else:
            # Es una publicación al canal/grupo, enviar anuncio completo
            await publisher_service.announce(
                platform="telegram",
                target_id=destino,
                book_data=meta,
                options={"message_thread_id": thread_id_destino, "state": user_state},
            )


async def descargar_epub_pendiente(
    update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int, job_queue=None
):
    """
    Función llamada cuando el usuario presiona "Descargar" en el menú intermedio.
    """
    from core.state_manager import state_manager

    user_state = state_manager.get_user_state(uid)

    bot = context.bot

    thread_id_origen = user_state.get(
        "message_thread_id"
    )  # Usar el guardado en el estado

    epub_buffer = user_state.pop("epub_buffer", None)
    epub_url = user_state.pop("epub_url", "")
    meta = user_state.pop("meta_pendiente", {})
    titulo = user_state.pop("titulo_pendiente", "")
    msg_id = user_state.pop("msg_botones_id", None)
    _msg_info_id = user_state.pop("msg_info_id", None)
    destino = user_state.get("destino") or update.effective_chat.id
    chat_origen = user_state.get("chat_origen") or destino

    # Solo usar thread_id si destino == chat_origen
    thread_id_destino = thread_id_origen if destino == chat_origen else None

    # API 9.3: Si es chat privado y es el origen, usar tópico de 'Mis Libros' para el archivo
    if uid == destino:
        from services.topic_service import topic_service

        topic_id = await topic_service.get_topic_id(uid, "mis_libros")
        if topic_id:
            thread_id_destino = topic_id

    # Identificar si es grupo
    is_group = update.effective_chat.type in ("group", "supergroup")
    is_authorized = is_authorized_group(chat_origen)

    # Si es grupo, se envía en el mismo grupo
    delete_seconds = 0
    if is_group:
        destino = chat_origen
        thread_id_destino = thread_id_origen
        # En grupos NO autorizados, se envía como archivo efímero con auto-borrado
        if not is_authorized:
            from services.settings_service import get_setting

            try:
                delete_minutes_str = get_setting("auto_delete_time", "2")
                delete_minutes = int(delete_minutes_str or "2")
                delete_seconds = max(60, delete_minutes * 60) if delete_minutes > 0 else 120
            except Exception:
                delete_seconds = 120

    # Borrar botones (siempre) para evitar doble click
    if msg_id:
        try:
            await bot.delete_message(chat_id=chat_origen, message_id=msg_id)
        except Exception as e:
            logger.debug("Could not delete msg_id %s: %s", msg_id, e)

    # Si eligió Volver, descartar buffer
    if update.callback_query and update.callback_query.data == "volver_ultima":
        return

    # Verificar que hay EPUB disponible
    if not epub_buffer:
        await bot.send_message(
            chat_id=chat_origen,
            text="⚠️ Lo sentimos, pero el archivo EPUB no está disponible en este momento. Inténtalo de nuevo más tarde o prueba con otro volumen. 🙏",
            message_thread_id=thread_id_origen,
        )
        return

    # Verificar cuota nuevamente
    if not await can_download(uid):
        await bot.send_message(
            chat_id=destino,
            text="🚫 ¡Vaya! Has alcanzado tu límite de descargas por hoy. Vuelve mañana para seguir explorando nuevas historias. ✨",
            message_thread_id=thread_id_destino,
        )
        return

    # Usar DeliveryService
    from services.delivery.delivery_service import delivery_service

    # Preparar datos
    book_data = {
        "title": titulo,
        "epub_buffer": epub_buffer,  # Bytes or Path
        "url": epub_url,
        **meta,  # Include all metadata
    }

    # Forzar que solo se envíe el mensaje del archivo con la info (1 solo mensaje)
    # Usamos <hr><hr> para que enviar_libro_directo salte Part 0 (Portada) y Part 1 (Sinopsis)
    from repositories.publication_repository import pub_repo
    from services.publisher.publisher_service import TelegramPublisherProvider

    try:
        db_templates = await pub_repo.get_templates(platform="telegram")
        info_t = next(
            (t for t in db_templates if (t.extra_config or {}).get("type") == "info"),
            None,
        )
        info_template = (
            info_t.content if info_t else TelegramPublisherProvider.INFO_TEMPLATE
        )
    except Exception as e:
        logger.warning(
            f"Error cargando plantilla de info de base de datos en descargar_epub_pendiente: {e}"
        )
        info_template = TelegramPublisherProvider.INFO_TEMPLATE

    # Botones de navegación integrados
    restantes = await downloads_left(uid)
    quota_text = ""
    if restantes != "ilimitadas":
        quota_text = f"\n\n📥 Te quedan {restantes} descargas disponibles para hoy."

    ephemeral_notice = ""
    if delete_seconds > 0:
        mins = max(1, delete_seconds // 60)
        ephemeral_notice = f"\n\n⏳ <i>Este archivo es efímero y se auto-eliminará en {mins} min.</i>"

    gratitude = (
        "\n\n✨ ¡Disfruta de tu lectura! Gracias por ser parte de nuestra comunidad. ❤️"
    )
    compact_caption = f"<hr><hr>{info_template}{quota_text}{ephemeral_notice}{gratitude}"

    keyboard = [
        [
            InlineKeyboardButton(
                "📚 Volver a categorías", callback_data="volver_colecciones"
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ Volver a la página anterior", callback_data="volver_ultima"
            )
        ],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")],
    ]

    # Intentar enviar
    success = await delivery_service.deliver(
        platform="telegram",
        target_id=uid,  # User ID for quota checks
        book_data=book_data,
        options={
            "target_chat_id": destino,  # Where to send the file
            "message_thread_id": thread_id_destino,
            "job_queue": job_queue or getattr(context, "job_queue", None),
            "auto_delete_seconds": delete_seconds,
            "caption": compact_caption,
            "reply_markup": InlineKeyboardMarkup(keyboard),  # Integrar botones aquí
        },
    )

    if success:
        # Gamificación: Hitos (No incluido en DeliveryService aún)
        from services.user_service import check_milestones

        milestone_msg = await check_milestones(uid, context)
        if milestone_msg:
            try:
                await bot.send_message(
                    chat_id=destino,
                    text=milestone_msg,
                    parse_mode="HTML",
                    message_thread_id=thread_id_destino,
                )
            except Exception:
                pass

        # --- Limpieza de mensajes antiguos de detalles ---
        # Si el envío fue exitoso, borramos los mensajes de la ficha (portada, sinopsis, info)
        # para evitar redundancia ya que el archivo trae su propia info.
        old_ids = user_state.pop("last_detalles_msg_ids", [])
        if old_ids and destino == chat_origen:
            for old_id in old_ids:
                try:
                    await bot.delete_message(chat_id=chat_origen, message_id=old_id)
                except Exception:
                    pass

    cleanup_tmp(epub_buffer)


async def enviar_libro_directo(
    bot,
    user_id: int,
    title: str,
    download_url: str | None,
    cover_url: str | None = None,
    target_chat_id: int | None = None,
    format_type: str = "standard",
    message_thread_id: int | None = None,
    metadata_override: dict[str, Any] | None = None,
    explicit_file_buffer: bytes | str | None = None,
    job_queue=None,
    auto_delete_seconds: int = 0,
    custom_caption: str | None = None,
    caption_template: str | None = None,
    reply_markup: Any | None = None,
):
    """
    Descarga y envía un libro directamente al usuario (para la Mini App).
    Replica el formato del bot: Portada -> Sinopsis -> Archivo.

    format_type: "standard", "fb_preview", "fb_direct"
    """
    try:
        # 1. Verificar límite
        if not await can_download(user_id):
            await bot.send_message(
                chat_id=user_id, text="🚫 Has alcanzado tu límite de descargas por hoy."
            )
            return False

        # Destino final del libro
        destino = target_chat_id if target_chat_id else user_id
        is_group_chat = str(destino).startswith("-")
        is_authorized = is_authorized_group(destino)

        # 2. Mensaje de preparación (efímero en grupos no autorizados para el usuario que interactúa)
        prep_msg = None
        try:
            api_kwargs_prep = (
                {"receiver_user_id": int(user_id)}
                if is_group_chat and user_id and not is_authorized
                else None
            )
            prep_msg = await bot.send_message(
                chat_id=destino,
                text=f"⏳ Estamos preparando tu lectura: <b>{title}</b>... ¡Solo un momento! 🚀",
                parse_mode="HTML",
                message_thread_id=message_thread_id,
                api_kwargs=api_kwargs_prep,
            )
        except Exception as e:
            logger.warning(f"No se pudo enviar mensaje de preparación: {e}")

        # 3. Obtener EPUB (Local o Servidor)
        epub_bytes = None

        if explicit_file_buffer:
            logger.info(f"Usando buffer explícito para: {title}")
            epub_bytes = explicit_file_buffer
        # Detectar si es ruta local absoluta (Compatible con Windows C:/ y Linux /)
        elif (
            download_url
            and not download_url.startswith("http")
            and os.path.isabs(download_url)
            and os.path.exists(download_url)
        ):
            logger.info(f"Usando archivo local: {download_url}")
            epub_bytes = download_url  # send_doc_bytes acepta rutas
        elif download_url:
            logger.info(f"Descargando EPUB desde: {download_url}")
            epub_bytes = await fetch_bytes(download_url, timeout=120)

        if not epub_bytes:
            error_msg = "❌ Error al obtener el archivo. No se encontró en el disco o la descarga falló."
            logger.error(f"EPUB acquisition failed for: {download_url}")
            await bot.send_message(
                chat_id=user_id,
                text=error_msg,
            )
            return False

        logger.info(f"EPUB listo para procesar: {download_url}")

        # 4. Parsear metadatos del EPUB
        if metadata_override:
            logger.info(f"Usando metadatos proporcionados para: {title}")
            logger.debug(
                f"metadata_override book_hash: {metadata_override.get('hash')}"
            )
            meta = metadata_override
        else:
            meta = {
                "titulo": title,
                "epub_version": "2.0",
                "fecha_modificacion": "Desconocida",
            }
            # Use centralized metadata enrichment
            from services.epub_service import enrich_metadata_from_epub

            logger.debug(f"Iniciando extracción de metadatos para: {title}")
            meta = await enrich_metadata_from_epub(epub_bytes, download_url, meta)
            logger.debug(
                f"Metadatos extraídos - titulo_serie: {meta.get('titulo_serie')}, "
                f"internal_title: {meta.get('internal_title')}, autor: {meta.get('autor')}"
            )

        # 5. Preparar Portada (desde ruta en LocalBook)
        cover_path = (
            meta.get("cover_original")
            or meta.get("cover_high")
            or meta.get("cover_medium")
            or meta.get("cover_low")
            or meta.get("cover")
        )
        portada_data = await resolve_cover_data(cover_path)
        if portada_data:
            logger.info("Portada lista para enviar")
        else:
            logger.info("Sin portada disponible, continuando sin ella")

        if not portada_data and cover_url:
            try:
                portada_data = await fetch_bytes(cover_url)
                logger.info(f"Portada descargada desde URL externa: {cover_url}")
            except Exception as e:
                logger.warning(f"No se pudo descargar portada desde URL externa: {e}")

        # --- CALCULAR TAMAÑO PARA PLANTILLAS ---
        if "file_size" not in meta:
            try:
                if isinstance(epub_bytes, bytes | bytearray):
                    meta["file_size"] = len(epub_bytes)
                elif isinstance(epub_bytes, str) and await asyncio.to_thread(
                    os.path.exists, epub_bytes
                ):
                    meta["file_size"] = await asyncio.to_thread(
                        os.path.getsize, epub_bytes
                    )
            except Exception as e:
                logger.warning(
                    f"No se pudo calcular el tamaño del archivo para meta: {e}"
                )

        # --- LOGICA FACEBOOK (Unificada con Template Engine) ---
        if format_type in ["fb_preview", "fb_direct"]:
            from services.publisher.facebook_publisher import (
                handle_facebook_publication,
            )

            return await handle_facebook_publication(
                bot=bot,
                user_id=user_id,
                format_type=format_type,
                title=title,
                download_url=download_url,
                cover_url=cover_url,
                meta=meta,
                portada_data=portada_data,
            )

        # --- CONSTRUIR RENDER RICH HTML UNIFICADO CON ARCHIVO INTEGRADO ---
        fname = meta.get("filename") or f"{title}.epub"
        if download_url and not download_url.startswith("http"):
            fname = os.path.basename(download_url)

        files = {}
        media = []

        if portada_data:
            if isinstance(portada_data, bytes):
                files["tomozaki_cover"] = ("cover.jpg", portada_data, "image/jpeg")
            elif isinstance(portada_data, str) and os.path.exists(portada_data):
                try:
                    with open(portada_data, "rb") as f:
                        files["tomozaki_cover"] = (
                            "cover.jpg",
                            f.read(),
                            "image/jpeg",
                        )
                except Exception as e:
                    logger.warning(f"Error al leer archivo de portada local: {e}")

            if "tomozaki_cover" in files:
                media.append(
                    {
                        "id": "tomozaki_cover",
                        "media": {"type": "photo", "media": "attach://tomozaki_cover"},
                    }
                )

        if epub_bytes:
            if isinstance(epub_bytes, (bytes, bytearray)):
                files["epub_file"] = (
                    fname,
                    io.BytesIO(epub_bytes),
                    "application/epub+zip",
                )
            elif isinstance(epub_bytes, str) and os.path.exists(epub_bytes):
                try:
                    with open(epub_bytes, "rb") as f:
                        files["epub_file"] = (fname, f.read(), "application/epub+zip")
                except Exception as e:
                    logger.warning(f"Error al leer archivo EPUB local: {e}")

            if "epub_file" in files:
                media.append(
                    {
                        "id": "epub_file",
                        "media": {"type": "document", "media": "attach://epub_file"},
                    }
                )

        from services.library_ui_service import build_book_rich_html
        html_content = build_book_rich_html(
            meta,
            has_cover=bool("tomozaki_cover" in files),
            include_download=bool("epub_file" in files),
            filename=fname,
        )

        # Intentar enviar Rich Message unificado con EPUB incluido
        rich_sent = False
        sent_doc = None
        from services.rich_message_service import RichMessageService

        # Soporte para Ephemeral Messages (Telegram Bot API 10.2 / Ephemeral Message Parameters)
        # En grupos NO autorizados, renderiza una respuesta privada visible ÚNICAMENTE para el usuario que interactuó.
        # En grupos autorizados por el admin o chats privados, se envía de forma regular.
        is_group_chat = str(destino).startswith("-")
        is_authorized = is_authorized_group(destino)
        api_kwargs = {}
        rich_kwargs = {}
        if is_group_chat and user_id and not is_authorized:
            api_kwargs["receiver_user_id"] = int(user_id)
            rich_kwargs["receiver_user_id"] = int(user_id)

        try:

            res = await RichMessageService.send_rich_message(
                chat_id=destino,
                html=html_content,
                media=media if media else None,
                files=files if files else None,
                reply_markup=reply_markup,
                message_thread_id=message_thread_id,
                **rich_kwargs,
            )
            if res and res.get("ok"):
                rich_sent = True
                sent_doc = res.get("result")
        except Exception as e:
            logger.warning(
                f"Error al enviar Rich Message unificado en enviar_libro_directo: {e}"
            )

        # Fallback tradicional SOLO si el Rich Message no se pudo enviar
        if not rich_sent:
            logger.info("Ejecutando fallback tradicional en enviar_libro_directo")
            from services.presentation.delivery_formatter import (
                build_telegram_delivery_parts,
            )

            msg_parts, fallback_caption, should_send_file_by_template = (
                build_telegram_delivery_parts(
                    meta=meta,
                    custom_caption=custom_caption,
                    caption_template=caption_template,
                )
            )
            if len(msg_parts) > 0:
                mensaje_portada = msg_parts[0]
                if portada_data and mensaje_portada:
                    await send_photo_bytes(
                        bot,
                        destino,
                        mensaje_portada,
                        portada_data,
                        filename="cover.jpg",
                        parse_mode="HTML",
                        message_thread_id=message_thread_id,
                        api_kwargs=api_kwargs,
                    )
                elif mensaje_portada:
                    await bot.send_message(
                        chat_id=destino,
                        text=mensaje_portada,
                        parse_mode="HTML",
                        message_thread_id=message_thread_id,
                        api_kwargs=api_kwargs,
                    )

            if len(msg_parts) > 1:
                sinopsis_to_send = msg_parts[1]
                if sinopsis_to_send:
                    await bot.send_message(
                        chat_id=destino,
                        text=sinopsis_to_send,
                        parse_mode="HTML",
                        message_thread_id=message_thread_id,
                        api_kwargs=api_kwargs,
                    )

            slug = meta.get("slug")
            if slug:
                final_caption = slug if slug.startswith("#") else f"#{slug}"
            else:
                title_en = meta.get("english_title") or meta.get("title") or title
                clean_title = re.sub(r"[^\w\s]", "", str(title_en)).replace(" ", "_")
                final_caption = f"#{clean_title}"

            if auto_delete_seconds > 0:
                mins = auto_delete_seconds // 60
                final_caption += f"\n\n🗑️ <i>Se borrará en {mins} min</i>"

            if epub_bytes:
                logger.info(f"Enviando archivo EPUB fallback a {destino}: {fname}")
                sent_doc = await send_doc_bytes(
                    bot,
                    destino,
                    final_caption,
                    epub_bytes,
                    filename=fname,
                    parse_mode="HTML",
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup,
                    api_kwargs=api_kwargs,
                )
            elif final_caption:
                await bot.send_message(
                    chat_id=destino,
                    text=final_caption,
                    parse_mode="HTML",
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup,
                    api_kwargs=api_kwargs,
                )

        if sent_doc and auto_delete_seconds > 0:
            msg_ids = []
            if isinstance(sent_doc, list):
                for m in sent_doc:
                    mid = (
                        m.get("message_id")
                        if isinstance(m, dict)
                        else getattr(m, "message_id", None)
                    )
                    if mid:
                        msg_ids.append(mid)
            else:
                mid = (
                    sent_doc.get("message_id")
                    if isinstance(sent_doc, dict)
                    else getattr(sent_doc, "message_id", None)
                )
                if mid:
                    msg_ids.append(mid)

            async def _do_delete(context_or_none=None):
                target_bot = getattr(context_or_none, "bot", bot)
                for mid in msg_ids:
                    try:
                        await target_bot.delete_message(
                            chat_id=destino, message_id=mid
                        )
                        logger.info(
                            f"Mensaje efímero {mid} borrado tras {auto_delete_seconds}s en chat {destino}"
                        )
                    except Exception as del_err:
                        logger.debug(
                            f"No se pudo auto-borrar mensaje efímero {mid}: {del_err}"
                        )

            if job_queue:
                async def _job_callback(ctx):
                    await _do_delete(ctx)

                job_queue.run_once(_job_callback, when=auto_delete_seconds)
            else:
                async def _asyncio_delete():
                    await asyncio.sleep(auto_delete_seconds)
                    await _do_delete()

                asyncio.create_task(_asyncio_delete())

        # 8. Registrar descarga e historial (Extraído a servicio dedicado)
        if sent_doc:
            from services.download_history import register_book_download

            await register_book_download(
                bot=bot,
                user_id=user_id,
                meta=meta,
                sent_doc=sent_doc,
                download_url=download_url,
                title=title,
            )

        # Limpieza
        try:
            if prep_msg:
                await bot.delete_message(
                    chat_id=user_id, message_id=prep_msg.message_id
                )
        except Exception as e:
            logger.debug(
                "Could not delete prep_msg %s: %s",
                getattr(prep_msg, "message_id", None) if prep_msg else "None",
                e,
            )

        return True

    except Exception as e:
        logger.error(f"Error en enviar_libro_directo: {e}", exc_info=True)
        await bot.send_message(
            chat_id=user_id, text=f"❌ Ocurrió un error interno: {e!s}"
        )
        return False


# Re-export FB functions from dedicated module for backward compatibility
from services.facebook_service import (  # noqa: F401
    _publish_choice_facebook,
    preparar_post_facebook,
    publicar_facebook_action,
)


async def _publish_choice_telegram(
    update, context: ContextTypes.DEFAULT_TYPE, uid: int
):
    """Continue publish flow for Telegram: send portada, sinopsis, info and buttons (omit FB post option)."""
    bot = context.bot

    from core.state_manager import state_manager

    st = state_manager.get_user_state(uid)
    st.pop("awaiting_publish_target", None)
    logger.debug(
        "_publish_choice_telegram: uid=%s pending=%s destino=%s chat_origen=%s",
        uid,
        st.get("pending_pub_book"),
        st.get("destino"),
        st.get("chat_origen"),
    )
    destino = st.get("destino") or update.effective_chat.id
    chat_origen = st.get("chat_origen") or destino
    thread_id_origen = st.get("message_thread_id")

    meta = st.get("meta_pendiente", {})
    epub_buffer = st.get("epub_buffer")

    # Intentar obtener plantilla por defecto para Telegram
    try:
        from repositories.publication_repository import pub_repo

        template = await pub_repo.get_default_template("telegram")
        caption_template = template.content if template else None
    except Exception as e:
        logger.debug("Error fetching default template: %s", e)
        caption_template = None

    # Usar enviar_libro_directo que ya maneja división por <hr>, slugs y plantillas
    success = await enviar_libro_directo(
        bot=bot,
        user_id=uid,
        title=meta.get("title", "Libro"),
        download_url=st.get("epub_url"),
        target_chat_id=destino,
        message_thread_id=thread_id_origen,
        metadata_override=meta,
        explicit_file_buffer=epub_buffer,
        caption_template=caption_template,
    )

    if not success:
        await bot.send_message(
            chat_id=chat_origen, text="❌ Error al procesar la publicación."
        )
        return

    # El bloque de sinopsis e info ya fue manejado por enviar_libro_directo vía msg_parts
    # conservamos solo la lógica de botones finales si es necesario

    # Los botones se envían al chat origen (privado) para control del usuario
    keyboard = [
        [InlineKeyboardButton("Descargar", callback_data="descargar_epub")],
        [InlineKeyboardButton("↩️ Volver", callback_data="volver_ultima")],
    ]

    try:
        sent = await bot.send_message(
            chat_id=chat_origen,
            text="¿Deseas descargar este EPUB en tu chat privado?",
            parse_mode="HTML",
            message_thread_id=thread_id_origen,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    except BadRequest as e:
        if "Message thread not found" in str(e) and thread_id_origen is not None:
            sent = await bot.send_message(
                chat_id=chat_origen,
                text="¿Deseas descargar este EPUB?",
                parse_mode="HTML",
                message_thread_id=None,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            raise
    st["msg_botones_id"] = sent.message_id
