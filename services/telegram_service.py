import asyncio
import io
import logging
import os
import re
from typing import Any


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

# from core.state_manager import state_manager (Moved to local scope)
# from core.session_manager import session_manager (Moved to local scope)
from config.config_settings import config
from utils.download_limiter import can_download, downloads_left, record_download

from utils.http_client import cleanup_tmp, fetch_bytes

logger = logging.getLogger(__name__)


async def resolve_cover_data(cover_path: str | None) -> bytes | str | None:
    """
    Resuelve la portada desde ruta o URL.
    - Si es URL de API (/api/...), la descarga desde el servidor local
    - Si es ruta local absoluta y existe, la usa directamente
    - Retorna bytes, ruta absoluta, o None
    """
    if not cover_path:
        return None

    # Si es URL de la API o HTTP, descargarla
    if cover_path.startswith("/api/") or cover_path.startswith("http"):
        try:
            # Construir URL completa si es relativa
            if cover_path.startswith("/api/"):
                # Usar localhost para peticiones internas (el servidor está en el mismo contenedor)
                cover_url_full = f"http://localhost:8000{cover_path}"
            else:
                cover_url_full = cover_path
            logger.info(f"Descargando portada desde URL: {cover_url_full}")
            return await fetch_bytes(cover_url_full)
        except Exception as e:
            logger.warning(f"Error descargando portada {cover_path}: {e}")
            return None

    # Si es ruta local absoluta
    if os.path.isabs(cover_path) and os.path.exists(cover_path):
        logger.info(f"Portada encontrada en ruta local: {cover_path}")
        return cover_path

    logger.warning(f"Portada no encontrada: {cover_path}")
    return None


async def send_photo_bytes(
    bot,
    chat_id,
    caption,
    data_or_path,
    filename="cover.jpg",
    parse_mode=None,
    message_thread_id=None,
    reply_markup=None,
):
    """Envía imagen desde bytes o ruta de archivo."""
    if not data_or_path:
        return None
    try:
        if isinstance(data_or_path, bytes | bytearray):
            bio = io.BytesIO(data_or_path)
            bio.name = filename
            bio.seek(0)
            input_file = InputFile(bio, filename=filename)
            try:
                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=input_file,
                    caption=caption,
                    parse_mode=parse_mode,
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup,
                )
            except BadRequest as e:
                if "Message thread not found" in str(e) and message_thread_id is not None:
                    # Retry without thread_id (send to General/Main)
                    bio.seek(0)
                    return await bot.send_photo(
                        chat_id=chat_id,
                        photo=input_file,
                        caption=caption,
                        parse_mode=parse_mode,
                        message_thread_id=None,
                        reply_markup=reply_markup,
                    )
                raise e

        elif isinstance(data_or_path, str) and await asyncio.to_thread(os.path.exists, data_or_path):
            # Read image file asynchronously into memory (covers are small)
            try:
                import aiofiles

                data_bytes = None
                async with aiofiles.open(data_or_path, "rb") as af:
                    data_bytes = await af.read()
                if data_bytes is not None:
                    bio = io.BytesIO(data_bytes)
                    bio.name = filename
                    bio.seek(0)
                    input_file = InputFile(bio, filename=filename)
                    try:
                        return await bot.send_photo(
                            chat_id=chat_id,
                            photo=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                        )
                    except BadRequest as e:
                        if "Message thread not found" in str(e) and message_thread_id is not None:
                            bio.seek(0)
                            return await bot.send_photo(
                                chat_id=chat_id,
                                photo=input_file,
                                caption=caption,
                                parse_mode=parse_mode,
                                message_thread_id=None,
                                reply_markup=reply_markup,
                            )
                        raise e
            except Exception:
                # Fallback to synchronous open if aiofiles fails
                with open(data_or_path, "rb") as f:
                    input_file = InputFile(f, filename=filename)
                    try:
                        return await bot.send_photo(
                            chat_id=chat_id,
                            photo=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                        )
                    except BadRequest as e:
                        if "Message thread not found" in str(e) and message_thread_id is not None:
                            f.seek(0)
                            return await bot.send_photo(
                                chat_id=chat_id,
                                photo=input_file,
                                caption=caption,
                                parse_mode=parse_mode,
                                message_thread_id=None,
                                reply_markup=reply_markup,
                            )
                        raise e
    except Exception as e:
        logger.debug(f"Error send_photo_bytes: {e}")
    return None


async def send_doc_bytes(
    bot,
    chat_id,
    caption,
    data_or_path,
    filename="file.epub",
    parse_mode=None,
    message_thread_id=None,
    reply_markup=None,
):
    """Envía documento EPUB desde bytes o ruta de archivo."""
    if not data_or_path:
        return None
    try:
        if isinstance(data_or_path, bytes | bytearray):
            bio = io.BytesIO(data_or_path)
            bio.name = filename
            bio.seek(0)
            input_file = InputFile(bio, filename=filename)
            try:
                return await bot.send_document(
                    chat_id=chat_id,
                    document=input_file,
                    caption=caption,
                    parse_mode=parse_mode,
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup,
                )
            except BadRequest as e:
                if "Message thread not found" in str(e) and message_thread_id is not None:
                    bio.seek(0)
                    return await bot.send_document(
                        chat_id=chat_id,
                        document=input_file,
                        caption=caption,
                        parse_mode=parse_mode,
                        message_thread_id=None,
                        reply_markup=reply_markup,
                    )
                raise e
        elif isinstance(data_or_path, str) and await asyncio.to_thread(os.path.exists, data_or_path):
            # Decide whether to load to memory or stream from disk
            try:
                size = await asyncio.to_thread(os.path.getsize, data_or_path)
            except Exception:
                size = None

            if size is not None and size <= config.MAX_IN_MEMORY_BYTES:
                # Small file: read async into memory then send
                try:
                    import aiofiles

                    async with aiofiles.open(data_or_path, "rb") as af:
                        data_read = await af.read()
                    bio = io.BytesIO(data_read)
                    bio.name = filename
                    bio.seek(0)
                    input_file = InputFile(bio, filename=filename)
                    try:
                        return await bot.send_document(
                            chat_id=chat_id,
                            document=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                        )
                    except BadRequest as e:
                        if "Message thread not found" in str(e) and message_thread_id is not None:
                            bio.seek(0)
                            return await bot.send_document(
                                chat_id=chat_id,
                                document=input_file,
                                caption=caption,
                                parse_mode=parse_mode,
                                message_thread_id=None,
                                reply_markup=reply_markup,
                            )
                        raise e
                except Exception:
                    pass

            # Large file: open synchronously (cheap) and let telegram lib stream it
            with open(data_or_path, "rb") as f:
                input_file = InputFile(f, filename=filename)
                try:
                    return await bot.send_document(
                        chat_id=chat_id,
                        document=input_file,
                        caption=caption,
                        parse_mode=parse_mode,
                        message_thread_id=message_thread_id,
                        reply_markup=reply_markup,
                    )
                except BadRequest as e:
                    if "Message thread not found" in str(e) and message_thread_id is not None:
                        f.seek(0)
                        return await bot.send_document(
                            chat_id=chat_id,
                            document=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=None,
                            reply_markup=reply_markup,
                        )
                    raise e
    except Exception as e:
        logger.debug(f"Error send_doc_bytes: {e}")
    return None


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
        series_id = user_state.get("series_id")
        volume_id = user_state.get("volume_id")
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
            epub_downloaded = await fetch_bytes(epub_url, timeout=120)

            if epub_downloaded:
                # Use orchestrator for enrichment
                meta = await metadata_orchestrator.get_enriched_metadata(book_id=epub_url, epub_bytes=epub_downloaded)

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
                await context.bot.delete_message(chat_id=menu_prep[0], message_id=menu_prep[1])
            except Exception:
                pass

        # 4. Announce Book using PublisherService
        await publisher_service.announce(
            platform="telegram",
            target_id=destino,
            book_data=meta,
            options={"message_thread_id": thread_id_destino, "state": user_state},
        )

        user_state["portada_pendiente"] = portada_url
        user_state["titulo_pendiente"] = titulo


async def descargar_epub_pendiente(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: int, job_queue=None):
    """
    Función llamada cuando el usuario presiona "Descargar" en el menú intermedio.
    """
    from core.state_manager import state_manager

    user_state = state_manager.get_user_state(uid)

    bot = context.bot

    thread_id_origen = user_state.get("message_thread_id")  # Usar el guardado en el estado

    epub_buffer = user_state.pop("epub_buffer", None)
    epub_url = user_state.pop("epub_url", "")
    meta = user_state.pop("meta_pendiente", {})
    titulo = user_state.pop("titulo_pendiente", "")
    msg_id = user_state.pop("msg_botones_id", None)
    msg_info_id = user_state.pop("msg_info_id", None)
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

    # Verificar privilegios usando el sistema de roles
    from services.user_service import get_effective_user

    user_info = await get_effective_user(uid)
    role = user_info.get("role", "free")
    is_privileged = role in ("admin", "staff")

    # Si es grupo y NO es privilegiado, forzar envío al privado
    if is_group and not is_privileged:
        destino = uid
        thread_id_destino = None
        # Opcional: Avisar en el grupo que se envió al privado?
        # Por ahora lo hacemos silencioso o asumimos que 'prep' message (line 564) iría al privado.
        # Pero wait, line 564 usa 'destino'. Si cambiamos destino a uid,
        # el mensaje "Preparando..." va al privado.
        # Eso es correcto.

    # Borrar botones (siempre)
    if msg_id:
        try:
            await bot.delete_message(chat_id=chat_origen, message_id=msg_id)
        except Exception as e:
            logger.debug("Could not delete msg_id %s: %s", msg_id, e)

    # Borrar mensaje de info (SOLO si NO es grupo)
    # En grupos queremos que persista para contexto
    if msg_info_id and not is_group:
        try:
            await bot.delete_message(chat_id=chat_origen, message_id=msg_info_id)
        except Exception as e:
            logger.debug("Could not delete msg_info_id %s: %s", msg_info_id, e)

    # Si eligió Volver, descartar buffer
    if update.callback_query.data == "volver_ultima":
        return

    # Verificar que hay EPUB disponible
    if not epub_buffer:
        await bot.send_message(
            chat_id=chat_origen,
            text="⚠️ EPUB no disponible.",
            message_thread_id=thread_id_origen,
        )
        return

    # Verificar cuota nuevamente
    if not await can_download(uid):
        await bot.send_message(
            chat_id=destino,
            text="🚫 Límite de descargas alcanzado.",
            message_thread_id=thread_id_destino,
        )
        return

    # Calculo de auto-borrado
    delete_seconds = 0
    if is_group and is_privileged and str(destino) == str(update.effective_chat.id):
        from services.settings_service import get_setting

        try:
            delete_minutes_str = get_setting("auto_delete_time", "2")
            delete_minutes = int(delete_minutes_str or "2")
            if delete_minutes > 0:
                delete_seconds = delete_minutes * 60
        except Exception:
            pass

    # Usar DeliveryService
    from services.delivery.delivery_service import delivery_service

    # Preparar datos
    book_data = {
        "title": titulo,
        "epub_buffer": epub_buffer,  # Bytes or Path
        "url": epub_url,
        **meta,  # Include all metadata
    }

    # Intentar enviar
    success = await delivery_service.deliver(
        platform="telegram",
        target_id=uid,  # User ID for quota checks
        book_data=book_data,
        options={
            "target_chat_id": destino,  # Where to send the file
            "message_thread_id": thread_id_destino,
            "job_queue": job_queue,
            "auto_delete_seconds": delete_seconds,
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

    cleanup_tmp(epub_buffer)

    if success:
        # --- Interactive Feedback (v6.1.0) ---
        # Mostrar botón de calificar si tenemos book_id local
        if epub_url and ("local_library" in epub_url or os.path.exists(epub_url)):
            try:
                from models.library_models import LocalBook
                from utils.library_db import get_session

                # Simple path matching.
                # Note: This session is sync, so we wrap or just use it quickly.
                session = get_session()
                book_db = session.query(LocalBook).filter_by(filepath=epub_url).first()
                if book_db:
                    kb_rate = [
                        [
                            InlineKeyboardButton(
                                "⭐ Calificar Libro",
                                callback_data=f"prompt_rate|{book_db.id}",
                            )
                        ]
                    ]
                    try:
                        await bot.send_message(
                            chat_id=destino,
                            text="¿Qué te pareció este libro?",
                            reply_markup=InlineKeyboardMarkup(kb_rate),
                            message_thread_id=thread_id_destino,
                        )
                    except Exception:
                        pass
                session.close()
            except Exception as e:
                logger.error(f"Error finding local book for rating: {e}")
        # -------------------------------------

    from utils.download_limiter import downloads_left

    restantes = await downloads_left(uid)

    # Mostrar descargas restantes (excepto Premium)
    if restantes != "ilimitadas":
        await bot.send_message(
            chat_id=destino,
            text=f"📥 Te quedan {restantes} descargas disponibles para hoy.",
            message_thread_id=thread_id_destino,
        )

    # Mostrar opciones finales
    keyboard = [
        [InlineKeyboardButton("📚 Volver a categorías", callback_data="volver_colecciones")],
        [InlineKeyboardButton("↩️ Volver a la página anterior", callback_data="volver_ultima")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")],
    ]
    await bot.send_message(
        chat_id=chat_origen,
        text="Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        message_thread_id=thread_id_origen,
    )


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
            await bot.send_message(chat_id=user_id, text="🚫 Has alcanzado tu límite de descargas por hoy.")
            return False

        # 2. Mensaje de preparación (siempre al usuario que interactúa)
        prep_msg = None
        try:
            prep_msg = await bot.send_message(chat_id=user_id, text=f"⏳ Procesando: {title}...")
        except Exception as e:
            logger.warning(f"No se pudo enviar mensaje de preparación: {e}")

        # Destino final del libro
        destino = target_chat_id if target_chat_id else user_id

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
            logger.debug(f"metadata_override book_hash: {metadata_override.get('hash')}")
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
            logger.info(f"Portada lista para enviar")
        else:
            logger.info(f"Sin portada disponible, continuando sin ella")

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
                elif isinstance(epub_bytes, str) and await asyncio.to_thread(os.path.exists, epub_bytes):
                    meta["file_size"] = await asyncio.to_thread(os.path.getsize, epub_bytes)
            except Exception as e:
                logger.warning(f"No se pudo calcular el tamaño del archivo para meta: {e}")

        from utils.template_engine import apply_publication_template

        # --- LOGICA FACEBOOK (Unificada con Template Engine) ---
        if format_type in ["fb_preview", "fb_direct"]:
            from services.publisher.publisher_service import TelegramPublisherProvider
            from utils.url_cache import create_short_url

            # Generar link público acortado
            dl_domain = config.DL_DOMAIN.rstrip("/")
            if not dl_domain.startswith("http"):
                dl_domain = f"https://{dl_domain}"
            try:
                url_hash = create_short_url(download_url, book_title=title)
                public_link = f"{dl_domain}/api/dl/{url_hash}"
            except Exception as e:
                logger.error("Error creating short URL: %s", e)
                public_link = download_url

            # Generar caption FB usando plantilla unificada
            fb_caption = apply_publication_template(
                TelegramPublisherProvider.FB_CAPTION_TEMPLATE, meta
            )
            # Limpiar HTML residual (FB no lo soporta)
            fb_caption = re.sub(r"<[^>]+>", "", fb_caption)
            # Añadir link de descarga
            fb_caption = f"{fb_caption}\n\n⬇️ Descarga: {public_link}"
            # Truncar si excede límite FB
            if len(fb_caption) > 2100:
                fb_caption = fb_caption[:2097] + "..."

            logger.debug(f"Caption FB generado vía template engine, longitud: {len(fb_caption)}")

            if format_type == "fb_preview":
                if portada_data:
                    await send_photo_bytes(bot, user_id, None, portada_data, filename="cover.jpg")
                await bot.send_message(
                    chat_id=user_id,
                    text=fb_caption,
                    disable_web_page_preview=False,
                )
            elif format_type == "fb_direct":
                from utils.helpers import validate_facebook_credentials
                is_valid, error_msg = validate_facebook_credentials(config)
                if not is_valid:
                    await bot.send_message(chat_id=user_id, text=error_msg, parse_mode="HTML")
                    return False

                fb_cover_url = cover_url or meta.get("portada")
                if not fb_cover_url or not fb_cover_url.startswith("http"):
                    await bot.send_message(
                        chat_id=user_id,
                        text="⚠️ No se pudo obtener una URL pública para la portada. Facebook requiere una URL pública.",
                    )
                    return False

                import httpx
                url = f"https://graph.facebook.com/{config.FACEBOOK_GROUP_ID}/photos"
                params = {
                    "url": fb_cover_url,
                    "caption": fb_caption,
                    "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN,
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(url, params=params, timeout=30)
                    if resp.status_code != 200:
                        logger.error(f"FB Error: {resp.text}")
                        await bot.send_message(
                            chat_id=user_id, text=f"❌ Error publicando en Facebook: {resp.text}"
                        )
                        return False
                await bot.send_message(
                    chat_id=user_id, text="✅ Publicado exitosamente en el Grupo de Facebook."
                )

        # --- PROCESAR CAPTION Y PLANTILLAS (Telegram) ---

        # Si no se provee nada, usamos el estándar del sistema (unificado)
        if not custom_caption and not caption_template:
            from services.publisher.publisher_service import TelegramPublisherProvider
            caption_template = f"{TelegramPublisherProvider.COVER_TEMPLATE}\n<hr>\n{TelegramPublisherProvider.SYNOPSIS_TEMPLATE}\n<hr>\n{TelegramPublisherProvider.INFO_TEMPLATE}"
            logger.info("Usando plantilla predeterminada del sistema para entrega directa.")

        source_text = caption_template or custom_caption
        msg_parts = []
        if source_text:
            msg_parts = re.split(r"<hr\s*/?>|---next---|---", source_text)
            msg_parts = [p.strip() for p in msg_parts if (p and p.strip())]

        # Aplicar el motor de plantillas a cada parte
        msg_parts = [apply_publication_template(p, meta) for p in msg_parts]
        logger.info(f"Mensaje procesado en {len(msg_parts)} partes")

        # Función para sanitizar HTML para Telegram
        def sanitize_tg_html(t: str) -> str:
            if not t:
                return ""
            t = re.sub(r"<(/?p|/?div|/?h\d|/?span|/?a[^>]*)>", "\n", t, flags=re.IGNORECASE)
            t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
            t = re.sub(r"<hr\s*/?>", "\n---\n", t, flags=re.IGNORECASE)
            t = re.sub(r"\n{3,}", "\n\n", t).strip()
            return t
        # 5. Enviar Portada
        if len(msg_parts) > 0:
            mensaje_portada = sanitize_tg_html(msg_parts[0])
            if portada_data:
                logger.info(f"Enviando portada a {destino}")
                await send_photo_bytes(
                    bot,
                    destino,
                    mensaje_portada,
                    portada_data,
                    filename="cover.jpg",
                    parse_mode="HTML",
                    message_thread_id=message_thread_id,
                )
            else:
                logger.info(f"Enviando mensaje de portada como texto a {destino}")
                await bot.send_message(
                    chat_id=destino,
                    text=mensaje_portada,
                    parse_mode="HTML",
                    message_thread_id=message_thread_id,
                )

        # 6. Enviar Sinopsis
        if len(msg_parts) > 1:
            sinopsis_to_send = sanitize_tg_html(msg_parts[1])
            if sinopsis_to_send:
                logger.info(f"Enviando sinopsis a {destino}")
                await bot.send_message(
                    chat_id=destino,
                    text=sinopsis_to_send,
                    parse_mode="HTML",
                    message_thread_id=message_thread_id,
                )

        # 7. Enviar Archivo EPUB
        final_caption = ""
        if len(msg_parts) > 2:
            final_caption = sanitize_tg_html(msg_parts[2])
        else:
            # Fallback mínimo si solo hay 1 o 2 partes
            final_caption = f"📂 <b>{title}</b>"

        if auto_delete_seconds > 0:
            mins = auto_delete_seconds // 60
            final_caption += f"\n\n🗑️ <i>Se borrará en {mins} min</i>"

        # Nombre de archivo - usar filename de LocalBook o extraer de ruta
        fname = meta.get("filename") or "archivo.epub"
        if download_url and not download_url.startswith("http"):
            fname = os.path.basename(download_url)

        logger.info(f"Enviando archivo EPUB a {destino}: {fname}")
        sent_doc = await send_doc_bytes(
            bot,
            destino,
            final_caption,
            epub_bytes,
            filename=fname,
            parse_mode="HTML",
            message_thread_id=message_thread_id,
            reply_markup=reply_markup,
        )

        if sent_doc and auto_delete_seconds > 0:
            if job_queue:
                job_queue.run_once(
                    lambda ctx: ctx.bot.delete_message(chat_id=destino, message_id=sent_doc.message_id),
                    when=auto_delete_seconds,
                )
            else:
                logger.warning("Auto-delete skipped: No job_queue provided")

        # Registrar en historial
        if sent_doc:
            from services.history_service import log_published_book

            file_info = {
                "file_size": sent_doc.document.file_size,
                "file_unique_id": sent_doc.document.file_unique_id,
            }
            try:
                log_published_book(
                    meta=meta,
                    message_id=sent_doc.message_id,
                    channel_id=sent_doc.chat.id,
                    file_info=file_info,
                )
            except Exception as e:
                logger.error(f"Failed to log book history in enviar_libro_directo: {e}")

            # 8. Registrar descarga y notificar
            await record_download(user_id)
            logger.info(f"[enviar_libro_directo] Descarga registrada para user {user_id}")

            # Gamificación: Incrementar contador total
            from services.user_service import increment_download_count

            try:
                await increment_download_count(user_id)
                logger.info(f"[enviar_libro_directo] Contador total incrementado para user {user_id}")
            except Exception as e:
                logger.error(f"[enviar_libro_directo] Error incrementando contador total: {e}")

            # Registrar en historial de descargas
            titulo_vol = meta.get("titulo_volumen") or meta.get("title") or meta.get("english_title") or title
            try:
                from repositories.download_repository import download_repo

                author = meta.get("autor", "Desconocido")

                # Enrich metadata if needed from title
                from utils.helpers import parse_metadata_from_title

                title_meta = parse_metadata_from_title(titulo_vol)

                romaji = meta.get("romaji_title") or title_meta.get("romaji")
                series = meta.get("titulo_serie") or title_meta.get("series")
                volume = meta.get("series_index") or title_meta.get("volume")
                clean_title = meta.get("internal_title") or title_meta.get("clean_title")
                translator = meta.get("traductor") or meta.get("publisher")

                # Generate stable hashes (only if not provided in override)
                from utils.helpers import generate_book_hash, generate_series_hash

                # CRITICAL: Prioritize hash from library (metadata_override)
                book_hash = meta.get("book_hash") or meta.get("hash")
                logger.debug(f"Hash from meta: {book_hash}")

                if not book_hash:
                    book_hash = generate_book_hash(
                        series=series,
                        author=author,
                        book_type=meta.get("book_type") or meta.get("categoria"),
                        volume=volume,
                        translator=translator,
                        layout_by=meta.get("maquetadores"),
                        language=meta.get("language"),
                    )
                    logger.warning(f"Generated new hash (should use library hash): {book_hash}")

                # ID extraction
                book_id_raw = meta.get("id") or meta.get("book_id")
                book_id_numeric = None
                if isinstance(book_id_raw, str) and book_id_raw.startswith("local_"):
                    try:
                        book_id_numeric = int(book_id_raw.replace("local_", ""))
                    except Exception:
                        pass
                elif isinstance(book_id_raw, int):
                    book_id_numeric = book_id_raw
                elif isinstance(book_id_raw, str) and book_id_raw.isdigit():
                    book_id_numeric = int(book_id_raw)

                await download_repo.add_download(
                    user_id=user_id,
                    title=titulo_vol,
                    author=author,
                    download_url=download_url,
                    file_size=meta.get("file_size"),
                    romaji_title=romaji,
                    series=series,
                    volume=volume,
                    translator=translator,
                    clean_title=clean_title,
                    book_hash=book_hash,
                    book_id=book_id_numeric,
                )

                # Also record in centralized metrics DB
                from repositories.metrics_repository import metrics_repo

                series_hash = meta.get("series_hash") or (
                    generate_series_hash(
                        series=series,
                        author=author,
                        book_type=meta.get("book_type") or meta.get("categoria"),
                    )
                    if series
                    else None
                )
                await metrics_repo.add_download(
                    user_id=user_id,
                    book_hash=book_hash,
                    series_hash=series_hash,
                    title=titulo_vol,
                )

                logger.info(f"[enviar_libro_directo] Historial guardado para user {user_id}: {titulo_vol}")
            except Exception as e:
                logger.error(
                    f"[enviar_libro_directo] Error saving download history for user {user_id}: {e}",
                    exc_info=True,
                )

            restantes = await downloads_left(user_id)
            if restantes != "ilimitadas":
                await bot.send_message(
                    chat_id=user_id,
                    text=f"📥 Te quedan {restantes} descargas disponibles para hoy.",
                )

        # Limpieza
        try:
            if prep_msg:
                await bot.delete_message(chat_id=user_id, message_id=prep_msg.message_id)
        except Exception as e:
            logger.debug(
                "Could not delete prep_msg %s: %s",
                getattr(prep_msg, "message_id", None) if prep_msg else "None",
                e,
            )

        return True

    except Exception as e:
        logger.error(f"Error en enviar_libro_directo: {e}", exc_info=True)
        await bot.send_message(chat_id=user_id, text=f"❌ Ocurrió un error interno: {str(e)}")
        return False


async def preparar_post_facebook(update, context: ContextTypes.DEFAULT_TYPE, uid: int):
    """Genera vista previa del post de Facebook."""
    bot = context.bot

    from core.state_manager import state_manager

    user_state = state_manager.get_user_state(uid)

    # Recuperar datos del estado
    meta = user_state.get("meta_pendiente", {})
    epub_url = user_state.get("epub_url", "")
    titulo = user_state.get("titulo_pendiente", "")

    if not epub_url:
        await bot.send_message(chat_id=uid, text="❌ No hay libro seleccionado.")
        return

    # Construir link público acortado con SHA256 persistente
    from utils.url_cache import create_short_url

    dl_domain = config.DL_DOMAIN.rstrip("/")
    if not dl_domain.startswith("http"):
        dl_domain = f"https://{dl_domain}"

    try:
        url_hash = create_short_url(epub_url, book_title=titulo)
    except Exception as e:
        logger.error("Error creando short URL: %s", e)
        await bot.send_message(
            chat_id=uid,
            text="❌ No fue posible generar el enlace acortado. Intenta de nuevo más tarde.",
        )
        return
    public_link = f"{dl_domain}/api/dl/{url_hash}"

    # Recuperar sinopsis si no está en meta
    sinopsis = meta.get("sinopsis") or meta.get("description")
    if not sinopsis:
        series_hash = user_state.get("series_hash")
        if series_hash:
            try:
                from repositories.series_repository import series_repo
                series_meta = await series_repo.get_by_hash(series_hash)
                if series_meta:
                    desc = getattr(series_meta, "description", None)
                    if desc:
                        meta["sinopsis"] = str(desc)
            except Exception:
                pass

    # Generar caption FB usando plantilla unificada
    from services.publisher.publisher_service import TelegramPublisherProvider
    from utils.template_engine import apply_publication_template

    fb_caption = apply_publication_template(
        TelegramPublisherProvider.FB_CAPTION_TEMPLATE, meta
    )
    # Limpiar HTML residual (FB no soporta)
    import re as _re
    fb_caption = _re.sub(r"<[^>]+>", "", fb_caption)
    fb_caption = f"<b>Vista Previa Facebook:</b>\n\n{fb_caption}\n\n⬇️ Descarga: {public_link}"


    # Guardar en estado para publicación
    user_state["fb_caption"] = fb_caption

    # Enviar vista previa (caption)
    btns = []
    btns.append([InlineKeyboardButton("🚀 Publicar ahora", callback_data="publicar_fb")])

    btns.append(
        [
            InlineKeyboardButton("🗑️ Descartar", callback_data="descartar_fb"),
            InlineKeyboardButton("↩️ Volver", callback_data="volver_ultima"),
        ]
    )

    logger.debug(
        "preparar_post_facebook: uid=%s preview_chat=%s thread=%s meta_title=%r",
        uid,
        user_state.get("publish_command_origin"),
        user_state.get("publish_command_thread_id"),
        titulo,
    )

    # Enviar como mensaje nuevo — preferir el chat donde se ejecutó el comando
    preview_chat = user_state.get("publish_command_origin") or uid
    preview_thread = user_state.get("publish_command_thread_id")
    await bot.send_message(
        chat_id=preview_chat,
        text=fb_caption,
        parse_mode="HTML",
        disable_web_page_preview=False,
        reply_markup=InlineKeyboardMarkup(btns),
        message_thread_id=preview_thread,
    )


async def _publish_choice_facebook(update, context: ContextTypes.DEFAULT_TYPE, uid: int):
    """Flow when a publisher chooses to publish on Facebook: send cover alone then prepare preview."""
    bot = context.bot

    from core.state_manager import state_manager

    st = state_manager.get_user_state(uid)

    # Clear awaiting flag (we're handling the choice now)
    st.pop("awaiting_publish_target", None)

    logger.debug(
        "_publish_choice_facebook: handling for uid=%s pending=%s",
        uid,
        st.get("pending_pub_book"),
    )

    # Borrar mensaje "Preparando..." si existe
    menu_prep = st.pop("pending_pub_menu_prep", None)
    if menu_prep:
        try:
            await bot.delete_message(chat_id=menu_prep[0], message_id=menu_prep[1])
        except Exception as e:
            logger.debug("No se pudo borrar mensaje 'Preparando...' (FB): %s", e)

    # If we have a pending_pub_book (set at selection), use it; otherwise rely on meta_pendiente
    pending = st.pop("pending_pub_book", None)
    epub_url = st.get("epub_url", "")
    epub_buffer = st.get("epub_buffer")
    meta = st.get("meta_pendiente", {})
    if pending:
        # populate ephemeral state for this publish flow
        st["titulo_pendiente"] = pending.get("titulo")
        st["portada_pendiente"] = pending.get("portada")
        epub_url = pending.get("href")
        st["epub_url"] = epub_url

    # Get cover from LocalBook path or URL
    cover_bytes = None
    cover_path = (
        meta.get("cover")
        or meta.get("cover_original")
        or meta.get("cover_high")
        or meta.get("cover_medium")
        or meta.get("cover_low")
    )
    if cover_path:
        cover_bytes = await resolve_cover_data(cover_path)

    # If cover not from path, try the pending portada or meta portada URL
    portada_url = pending.get("portada") if pending else meta.get("portada")
    if not cover_bytes and portada_url:
        cover_bytes = await fetch_bytes(portada_url)

    # If we still don't have metadata, try to fetch EPUB to build meta
    if not meta and epub_url:
        epub_downloaded = await fetch_bytes(epub_url, timeout=60)
        if epub_downloaded:
            st["epub_buffer"] = epub_downloaded
            epub_buffer = epub_downloaded
            # Use centralized metadata enrichment
            from services.epub_service import enrich_metadata_from_epub

            meta = await enrich_metadata_from_epub(epub_downloaded, epub_url, meta)
            st["meta_pendiente"] = meta

    logger.debug(
        "_publish_choice_facebook: sending cover to origin=%s (thread=%s), have_cover=%s",
        st.get("publish_command_origin"),
        st.get("publish_command_thread_id"),
        bool(cover_bytes),
    )

    # Send only cover (no caption) if available
    if cover_bytes:
        # send the cover to the chat where the publisher invoked the command, default to uid
        dest_chat = st.get("publish_command_origin") or uid
        thread = st.get("publish_command_thread_id")
        await send_photo_bytes(
            bot,
            dest_chat,
            caption=None,
            data_or_path=cover_bytes,
            filename="cover.jpg",
            parse_mode=None,
            message_thread_id=thread,
        )
        # If cover was a temp file path, cleanup
        if isinstance(cover_bytes, str):
            cleanup_tmp(cover_bytes)

    # Now prepare and send the FB preview text to the publisher (private chat)
    await preparar_post_facebook(update, context, uid)

    # cleanup pending menu_prep
    st.pop("pending_pub_menu_prep", None)
    st.pop("publish_command_origin", None)
    st.pop("publish_command_thread_id", None)


async def _publish_choice_telegram(update, context: ContextTypes.DEFAULT_TYPE, uid: int):
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
        caption_template=caption_template
    )

    if not success:
        await bot.send_message(chat_id=chat_origen, text="❌ Error al procesar la publicación.")
        return

    # El bloque de sinopsis e info ya fue manejado por enviar_libro_directo vía msg_parts
    # conservamos solo la lógica de botones finales si es necesario

    # Los botones se envían al chat origen (privado) para control del usuario
    keyboard = [
        [InlineKeyboardButton("📥 Descargar EPUB", callback_data="descargar_epub")],
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
        st["msg_botones_id"] = sent.message_id
    except BadRequest as e:
        if "Message thread not found" in str(e) and thread_id_origen is not None:
            await bot.send_message(
                chat_id=chat_origen,
                text="¿Deseas descargar este EPUB?",
                parse_mode="HTML",
                message_thread_id=None,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            raise e
        if "Message thread not found" in str(e) and thread_id_origen is not None:
            sent = await bot.send_message(
                chat_id=chat_origen,
                text="¿Deseas descargar este EPUB?",
                parse_mode="HTML",
                message_thread_id=None,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            raise e
    st["msg_botones_id"] = sent.message_id


async def publicar_facebook_action(update, context: ContextTypes.DEFAULT_TYPE, uid: int):
    """Publica el post en Facebook."""
    bot = context.bot

    from core.state_manager import state_manager
    from services.publisher.publisher_service import publisher_service

    user_state = state_manager.get_user_state(uid)

    caption = user_state.get("fb_caption")
    if not caption:
        await bot.send_message(chat_id=uid, text="❌ No hay post preparado.")
        return

    # Send progress message
    publish_chat = user_state.get("publish_command_origin") or update.effective_chat.id or uid
    publish_thread = user_state.get("publish_command_thread_id")
    try:
        await bot.send_message(
            chat_id=publish_chat,
            text="⏳ Publicando en Facebook...",
            message_thread_id=publish_thread,
        )
    except BadRequest:
        # Retry without thread if failed (similar to original logic but simpler)
        try:
            await bot.send_message(
                chat_id=publish_chat,
                text="⏳ Publicando en Facebook...",
                message_thread_id=None,
            )
        except Exception:
            pass

    # Prepare data for publisher
    # Publisher needs cover_url and caption
    book_data = {
        "cover_url": user_state.get("portada_pendiente"),
        "cover": user_state.get("portada_pendiente"),  # Fallback key
        # We pass other meta just in case, but caption is explict
    }

    options = {"caption": caption}

    success = await publisher_service.announce(
        "facebook",
        target_id=uid,  # Not used by FB provider technically (it uses config Group ID), but required by interface
        book_data=book_data,
        options=options,
    )

    if success:
        await bot.send_message(
            chat_id=uid,
            text="✅ Publicado exitosamente en el Grupo de Facebook.",
        )
    else:
        await bot.send_message(
            chat_id=uid,
            text="❌ Error publicando en Facebook. Ver logs.",
        )
