"""
Cover & media sending utilities.

Extracted from telegram_service.py to reduce module size.
Provides:
  - resolve_cover_data: Resolve cover from local path or URL
  - send_photo_bytes: Send photo via Telegram bot from bytes/path
  - send_doc_bytes: Send document via Telegram bot from bytes/path
"""

import asyncio
import io
import logging
import os

from telegram import InputFile
from telegram.error import BadRequest

from config.config_settings import config
from utils.http_client import fetch_bytes

logger = logging.getLogger(__name__)


async def resolve_cover_data(cover_path: str | None) -> bytes | str | None:
    """
    Resuelve la portada desde ruta o URL.
    - Si es URL de API (/api/...), la descarga desde el servidor local o la lee de disco si es posible
    - Si es ruta local absoluta y existe, la usa directamente
    - Retorna bytes, ruta absoluta, o None
    """
    if not cover_path:
        return None

    # Optimización de alto rendimiento: Traducir rutas relativas de covers directamente al disco local
    if cover_path.startswith("/api/library/covers/"):
        filename = os.path.basename(cover_path)
        from utils.library_db import COVERS_DIR
        local_path = os.path.join(COVERS_DIR, filename)
        if os.path.exists(local_path):
            logger.info(f"🚀 Portada resuelta directamente de disco local: {local_path}")
            return local_path

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


# Caché global en memoria de file_ids de portadas de Telegram
_cover_file_id_cache: dict[str, str] = {}


def get_cached_cover_file_id(key: str) -> str | None:
    """Obtiene el file_id cacheado para una ruta o identificador de portada."""
    return _cover_file_id_cache.get(key)


def set_cached_cover_file_id(key: str, file_id: str) -> None:
    """Guarda un file_id de Telegram en la caché."""
    if key and file_id:
        _cover_file_id_cache[key] = file_id


async def send_photo_bytes(
    bot,
    chat_id,
    caption,
    data_or_path,
    filename="cover.jpg",
    parse_mode=None,
    message_thread_id=None,
    reply_markup=None,
    api_kwargs=None,
):
    """Envía imagen desde file_id cacheado, bytes o ruta de archivo."""
    if not data_or_path:
        return None

    cache_key = str(data_or_path) if isinstance(data_or_path, str) else filename

    # 1. Optimización: Si ya tenemos un file_id de Telegram para esta portada, enviarlo directamente
    cached_file_id = _cover_file_id_cache.get(cache_key)
    if cached_file_id:
        try:
            logger.debug(f"⚡ Reutilizando file_id de Telegram para portada: {cached_file_id[:15]}...")
            return await bot.send_photo(
                chat_id=chat_id,
                photo=cached_file_id,
                caption=caption,
                parse_mode=parse_mode,
                message_thread_id=message_thread_id,
                reply_markup=reply_markup,
                api_kwargs=api_kwargs,
            )
        except Exception as e:
            logger.debug(f"file_id inválido o expirado, recurriendo a subida: {e}")
            _cover_file_id_cache.pop(cache_key, None)

    # 2. Si data_or_path es directamente un file_id (no existe como archivo local)
    if isinstance(data_or_path, str) and not os.path.exists(data_or_path) and not data_or_path.startswith("/") and not data_or_path.startswith("http") and not (len(data_or_path) > 1 and data_or_path[1] == ":"):
        try:
            return await bot.send_photo(
                chat_id=chat_id,
                photo=data_or_path,
                caption=caption,
                parse_mode=parse_mode,
                message_thread_id=message_thread_id,
                reply_markup=reply_markup,
                api_kwargs=api_kwargs,
            )
        except Exception as e:
            logger.debug(f"Error enviando portada como file_id directo: {e}")

    try:
        sent_msg = None
        if isinstance(data_or_path, bytes | bytearray):
            bio = io.BytesIO(data_or_path)
            bio.name = filename
            bio.seek(0)
            input_file = InputFile(bio, filename=filename)
            try:
                sent_msg = await bot.send_photo(
                    chat_id=chat_id,
                    photo=input_file,
                    caption=caption,
                    parse_mode=parse_mode,
                    message_thread_id=message_thread_id,
                    reply_markup=reply_markup,
                    api_kwargs=api_kwargs,
                )
            except BadRequest as e:
                if api_kwargs:
                    try:
                        bio.seek(0)
                        sent_msg = await bot.send_photo(
                            chat_id=chat_id,
                            photo=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                        )
                    except Exception:
                        pass
                if not sent_msg and "Message thread not found" in str(e) and message_thread_id is not None:
                    bio.seek(0)
                    sent_msg = await bot.send_photo(
                        chat_id=chat_id,
                        photo=input_file,
                        caption=caption,
                        parse_mode=parse_mode,
                        message_thread_id=None,
                        reply_markup=reply_markup,
                    )
                if not sent_msg:
                    raise e

        elif isinstance(data_or_path, str) and await asyncio.to_thread(os.path.exists, data_or_path):
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
                        sent_msg = await bot.send_photo(
                            chat_id=chat_id,
                            photo=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                            api_kwargs=api_kwargs,
                        )
                    except BadRequest as e:
                        if "Message thread not found" in str(e) and message_thread_id is not None:
                            bio.seek(0)
                            sent_msg = await bot.send_photo(
                                chat_id=chat_id,
                                photo=input_file,
                                caption=caption,
                                parse_mode=parse_mode,
                                message_thread_id=None,
                                reply_markup=reply_markup,
                                api_kwargs=api_kwargs,
                            )
                        else:
                            raise e
            except Exception:
                with open(data_or_path, "rb") as f:
                    input_file = InputFile(f, filename=filename)
                    try:
                        sent_msg = await bot.send_photo(
                            chat_id=chat_id,
                            photo=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                            api_kwargs=api_kwargs,
                        )
                    except BadRequest as e:
                        if "Message thread not found" in str(e) and message_thread_id is not None:
                            f.seek(0)
                            sent_msg = await bot.send_photo(
                                chat_id=chat_id,
                                photo=input_file,
                                caption=caption,
                                parse_mode=parse_mode,
                                message_thread_id=None,
                                reply_markup=reply_markup,
                                api_kwargs=api_kwargs,
                            )
                        else:
                            raise e

        # Guardar el file_id en caché para próximas visualizaciones
        if sent_msg and hasattr(sent_msg, "photo") and sent_msg.photo:
            new_file_id = sent_msg.photo[-1].file_id
            _cover_file_id_cache[cache_key] = new_file_id

        return sent_msg
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
    api_kwargs=None,
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
                    api_kwargs=api_kwargs,
                )
            except BadRequest as e:
                if api_kwargs:
                    try:
                        bio.seek(0)
                        return await bot.send_document(
                            chat_id=chat_id,
                            document=input_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            message_thread_id=message_thread_id,
                            reply_markup=reply_markup,
                        )
                    except Exception:
                        pass
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
                            api_kwargs=api_kwargs,
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
                                api_kwargs=api_kwargs,
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
                        api_kwargs=api_kwargs,
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
                            api_kwargs=api_kwargs,
                        )
                    raise e
    except Exception as e:
        logger.debug(f"Error send_doc_bytes: {e}")
    return None
