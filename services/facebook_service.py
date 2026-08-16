"""
Facebook publishing service — extracted from telegram_service.py.

Contains all Facebook-related flows:
- preparar_post_facebook: Generates FB preview in Telegram chat
- _publish_choice_facebook: Handles publisher's "Facebook" choice flow
- publicar_facebook_action: Publishes prepared post to Facebook Group
"""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from config.config_settings import config

logger = logging.getLogger(__name__)


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
    from utils.helpers import clean_caption_for_facebook
    from utils.template_engine import apply_publication_template

    raw_fb_caption = apply_publication_template(TelegramPublisherProvider.FB_CAPTION_TEMPLATE, meta)
    fb_caption_text = clean_caption_for_facebook(raw_fb_caption, public_link=public_link)
    fb_caption = f"<b>Vista Previa Facebook:</b>\n\n{fb_caption_text}"

    # Guardar en estado para publicación
    user_state["fb_caption"] = fb_caption

    # Enviar vista previa (caption)
    btns = [
        [InlineKeyboardButton("🚀 Publicar ahora", callback_data="publicar_fb")],
        [
            InlineKeyboardButton("🗑️ Descartar", callback_data="descartar_fb"),
            InlineKeyboardButton("↩️ Volver", callback_data="volver_ultima"),
        ],
    ]

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
    from services.cover_service import resolve_cover_data, send_photo_bytes
    from utils.http_client import cleanup_tmp, fetch_bytes

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
        # Retry without thread if failed
        try:
            await bot.send_message(
                chat_id=publish_chat,
                text="⏳ Publicando en Facebook...",
                message_thread_id=None,
            )
        except Exception:
            pass

    # Prepare data for publisher
    book_data = {
        "cover_url": user_state.get("portada_pendiente"),
        "cover": user_state.get("portada_pendiente"),
    }

    options = {"caption": caption}

    success = await publisher_service.announce(
        "facebook",
        target_id=uid,
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
