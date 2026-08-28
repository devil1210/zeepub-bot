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
                    api_kwargs=api_kwargs,
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
                        api_kwargs=api_kwargs,
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
                            api_kwargs=api_kwargs,
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
                                api_kwargs=api_kwargs,
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
                            api_kwargs=api_kwargs,
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
                                api_kwargs=api_kwargs,
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
