import logging
import re
from typing import Any

from services.publisher.publisher_service import TelegramPublisherProvider
from utils.template_engine import apply_publication_template

logger = logging.getLogger(__name__)


def build_telegram_delivery_parts(
    meta: dict[str, Any], custom_caption: str | None = None, caption_template: str | None = None
) -> tuple[list[str], str, bool]:
    """
    Construye las partes del mensaje para Telegram y determina si se debe adjuntar el archivo.
    Returns:
        (msg_parts: list[str], final_caption: str, should_send_file: bool)
    """
    if not custom_caption and not caption_template:
        caption_template = f"{TelegramPublisherProvider.COVER_TEMPLATE}\n<hr>\n{TelegramPublisherProvider.SYNOPSIS_TEMPLATE}\n<hr>\n{TelegramPublisherProvider.INFO_TEMPLATE}"
        logger.info("Usando plantilla predeterminada del sistema para entrega directa.")

    source_text = caption_template or custom_caption
    msg_parts = []
    if source_text:
        # Detectar si empieza por separadores (indica que queremos saltar partes)
        starts_with_sep = source_text.startswith("<hr>") or source_text.startswith("---")
        msg_parts = re.split(r"<hr\s*/?>|---next---|---", source_text)

        if starts_with_sep:
            msg_parts = [p.strip() for p in msg_parts]
        else:
            msg_parts = [p.strip() for p in msg_parts if p.strip()]

    # Aplicar el motor de plantillas a cada parte
    msg_parts = [apply_publication_template(p, meta) for p in msg_parts]
    logger.info(f"Mensaje procesado en {len(msg_parts)} partes")

    # Determine default final_caption before processing signals
    final_caption = ""
    if len(msg_parts) > 2:
        final_caption = msg_parts[2]
    else:
        # Fallback mínimo si solo hay 1 o 2 partes
        titulo = meta.get("titulo", "Libro")
        final_caption = f"📂 <b>{titulo}</b>"

    # Buscar señal de adjunto archivo
    attach_signal = "__ATTACH_FILE_SIGNAL__"
    should_send_file_by_template = False

    for i, part in enumerate(msg_parts):
        if attach_signal in part:
            should_send_file_by_template = True
            msg_parts[i] = part.replace(attach_signal, "").strip()

    if attach_signal in final_caption:
        should_send_file_by_template = True
        final_caption = final_caption.replace(attach_signal, "").strip()

    # Función para sanitizar HTML para Telegram
    def sanitize_tg_html(t: str) -> str:
        if not t:
            return ""
        t = re.sub(r"<(/?p|/?div|/?h\d|/?span|/?a[^>]*)>", "\n", t, flags=re.IGNORECASE)
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.IGNORECASE)
        t = re.sub(r"<hr\s*/?>", "\n---\n", t, flags=re.IGNORECASE)
        t = re.sub(r"\n{3,}", "\n\n", t).strip()
        return t

    msg_parts = [sanitize_tg_html(p) for p in msg_parts]
    final_caption = sanitize_tg_html(final_caption)

    # Re-assign sanitized parts
    if len(msg_parts) > 2:
        msg_parts[2] = final_caption

    return msg_parts, final_caption, should_send_file_by_template
