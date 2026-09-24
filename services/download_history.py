# services/download_history.py

from typing import Any

from utils.logger import logger


async def register_book_download(
    bot,
    user_id: int,
    meta: dict[str, Any],
    sent_doc: Any,
    download_url: str | None,
    title: str,
    target_chat_id: int | str | None = None,
    message_thread_id: int | None = None,
) -> None:
    """
    Registra una descarga exitosa:
    1. Loguea en history_service (base de datos de publicaciones)
    2. Incrementa límites diarios (download_limiter)
    3. Incrementa estadísticas de usuario (user_service)
    4. Registra descarga detallada (download_repo)
    5. Registra en métricas globales (metrics_repo)
    6. Notifica descargas restantes al usuario
    """
    if not sent_doc:
        return

    # 1. Registrar en historial de publicaciones (history_service)
    try:
        from services.history_service import log_published_book

        doc_item = (
            sent_doc[-1]
            if isinstance(sent_doc, list) and len(sent_doc) > 0
            else sent_doc
        )
        msg_id = getattr(doc_item, "message_id", None) or (
            doc_item.get("message_id") if isinstance(doc_item, dict) else None
        )
        chat_obj = getattr(doc_item, "chat", None)
        chan_id = (
            getattr(chat_obj, "id", None)
            if chat_obj
            else (
                doc_item.get("chat", {}).get("id")
                if isinstance(doc_item, dict)
                else user_id
            )
        )

        doc_obj = getattr(doc_item, "document", None) or (
            doc_item.get("document") if isinstance(doc_item, dict) else None
        )
        file_info = {}
        if doc_obj:
            file_info = {
                "file_size": getattr(doc_obj, "file_size", None)
                or (
                    doc_obj.get("file_size")
                    if isinstance(doc_obj, dict)
                    else meta.get("file_size")
                ),
                "file_unique_id": getattr(doc_obj, "file_unique_id", None)
                or (
                    doc_obj.get("file_unique_id") if isinstance(doc_obj, dict) else None
                ),
            }

        if msg_id and chan_id:
            log_published_book(
                meta=meta,
                message_id=msg_id,
                channel_id=chan_id,
                file_info=file_info,
            )
    except Exception as e:
        logger.error(f"Failed to log book history: {e}")

    # 2. Registrar descarga y notificar (download_limiter)
    try:
        from utils.download_limiter import downloads_left, record_download

        await record_download(user_id)
        logger.info(f"Descarga registrada para user {user_id}")
    except Exception as e:
        logger.error(f"Error registrando descarga: {e}")

    # 3. Gamificación: Incrementar contador total (user_service)
    try:
        from services.user_service import increment_download_count

        await increment_download_count(user_id)
        logger.info(f"Contador total incrementado para user {user_id}")
    except Exception as e:
        logger.error(f"Error incrementando contador total: {e}")

    # 4. Registrar en historial detallado de descargas (download_repo y metrics_repo)
    try:
        titulo_vol = (
            meta.get("titulo_volumen")
            or meta.get("title")
            or meta.get("english_title")
            or title
        )
        author = meta.get("autor", "Desconocido")

        # Enrich metadata if needed from title
        from utils.helpers import parse_metadata_from_title

        title_meta = parse_metadata_from_title(titulo_vol)

        romaji = meta.get("romaji_title") or title_meta.get("romaji")
        series = meta.get("titulo_serie") or title_meta.get("series")
        volume = meta.get("series_index") or title_meta.get("volume")
        clean_title = meta.get("internal_title") or title_meta.get("clean_title")
        translator = meta.get("traductor") or meta.get("publisher")

        # Hash handling
        from utils.helpers import generate_book_hash, generate_series_hash

        book_hash = meta.get("book_hash") or meta.get("hash")

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
            logger.warning(f"Generated new hash: {book_hash}")

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

        # Download Repository
        from repositories.download_repository import download_repo

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

        # Metrics Repository
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

        logger.info(f"Historial guardado para user {user_id}: {titulo_vol}")

        # 5. Notificar descargas restantes
        from utils.download_limiter import downloads_left

        restantes = await downloads_left(user_id)
        if restantes != "ilimitadas":
            quota_text = f"📥 Te quedan {restantes} descargas disponibles para hoy."
            dest_chat = target_chat_id or chan_id or user_id
            is_group_chat = str(dest_chat).startswith("-")

            if is_group_chat:
                try:
                    await bot.send_message(
                        chat_id=dest_chat,
                        text=quota_text,
                        reply_to_message_id=msg_id,
                        message_thread_id=message_thread_id,
                        api_kwargs={"receiver_user_id": int(user_id)},
                    )
                    logger.info(
                        f"Mensaje efímero de saldo ({restantes} restantes) enviado a user {user_id} en grupo {dest_chat}"
                    )
                except Exception as e:
                    logger.warning(
                        f"No se pudo enviar mensaje efímero de saldo a {user_id} en grupo {dest_chat}: {e}"
                    )
            else:
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=quota_text,
                    )
                except Exception as e:
                    logger.warning(f"Error enviando saldo en privado a {user_id}: {e}")

    except Exception as e:
        logger.error(f"Error saving download history: {e}", exc_info=True)
