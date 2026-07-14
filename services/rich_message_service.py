# services/rich_message_service.py
#
# Servicio para gestionar el renderizado y envío de Rich Messages (API 10.2).
# Single Responsibility: Proveer los builders de bloques y transporte HTTP directo.
#

import logging
import re
import httpx
from config.config_settings import config

logger = logging.getLogger(__name__)


class RichMessageService:
    """
    Servicio unificado de Rich Messages.
    Permite enviar mensajes estructurados en bloques nativos a través de la API 10.2 de Telegram.
    """

    @classmethod
    async def send_rich_message(cls, chat_id: int | str, blocks: list[dict], **kwargs) -> dict | None:
        """
        Envía un mensaje enriquecido al chat especificado usando POST directo.
        """
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendRichMessage"
        payload = {
            "chat_id": chat_id,
            "rich_message": {
                "blocks": blocks
            },
            **kwargs
        }
        if "reply_markup" in payload:
            markup = payload["reply_markup"]
            if hasattr(markup, "to_dict"):
                payload["reply_markup"] = markup.to_dict()
        try:
            logger.info(f"[RichMessageService] Enviando payload: {payload}")
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"[RichMessageService] Error en sendRichMessage: {result}")
                return result
        except Exception as e:
            logger.error(f"[RichMessageService] Excepción de transporte en sendRichMessage: {e}", exc_info=True)
            return None

    @classmethod
    async def send_rich_message_draft(cls, chat_id: int | str, blocks: list[dict], draft_id: str | None = None, **kwargs) -> dict | None:
        """
        Envía o actualiza un borrador enriquecido (AI Streaming) usando POST directo.
        """
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendRichMessageDraft"
        payload = {
            "chat_id": chat_id,
            "rich_message": {
                "blocks": blocks
            },
            **kwargs
        }
        if "reply_markup" in payload:
            markup = payload["reply_markup"]
            if hasattr(markup, "to_dict"):
                payload["reply_markup"] = markup.to_dict()
        if draft_id:
            payload["draft_id"] = draft_id
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"[RichMessageService] Error en sendRichMessageDraft: {result}")
                return result
        except Exception as e:
            logger.error(f"[RichMessageService] Excepción de transporte en sendRichMessageDraft: {e}", exc_info=True)
            return None

    @classmethod
    async def edit_rich_message(cls, chat_id: int | str, message_id: int, blocks: list[dict], reply_markup=None) -> dict | None:
        """
        Edita un mensaje existente para transformarlo en un Rich Message.
        """
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "rich_message": {
                "blocks": blocks
            }
        }
        if reply_markup:
            if hasattr(reply_markup, "to_dict"):
                payload["reply_markup"] = reply_markup.to_dict()
            else:
                payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"[RichMessageService] Error en editMessageText (Rich): {result}")
                return result
        except Exception as e:
            logger.error(f"[RichMessageService] Excepción de transporte en editMessageText: {e}", exc_info=True)
            return None

    # ── Builders de Bloques ──────────────────────────────────────────────────

    @classmethod
    def create_paragraph(cls, text: str | dict) -> dict:
        """Crea un bloque de párrafo. Acepta texto plano o diccionario RichText."""
        rich_text = text if isinstance(text, dict) else {"text": text}
        return {
            "type": "paragraph",
            "text": rich_text
        }

    @classmethod
    def create_section_heading(cls, text: str | dict, level: int = 1) -> dict:
        """Crea un encabezado de sección (nivel 1 a 6)."""
        rich_text = text if isinstance(text, dict) else {"text": text}
        return {
            "type": "section_heading",
            "text": rich_text,
            "level": max(1, min(6, level))
        }

    @classmethod
    def create_table(cls, headers: list[str], rows: list[list[str]], caption: str | None = None) -> dict:
        """
        Crea un bloque de tabla responsivo.
        """
        table_rows = []
        # Cabecera
        header_cells = [{"text": {"text": h}} for h in headers]
        table_rows.append({"cells": header_cells, "is_header": True})
        # Filas
        for row in rows:
            cells = [{"text": {"text": str(c)}} for c in row]
            table_rows.append({"cells": cells})

        table_block = {
            "type": "table",
            "rows": table_rows
        }
        if caption:
            table_block["caption"] = {"text": caption}
        return table_block

    @classmethod
    def create_details(cls, title: str | dict, blocks: list[dict], is_open: bool = False) -> dict:
        """Crea un bloque colapsable de detalles."""
        rich_summary = title if isinstance(title, dict) else {"text": title}
        return {
            "type": "details",
            "summary": rich_summary,
            "blocks": blocks,
            "is_open": is_open
        }

    @classmethod
    def create_thinking(cls) -> dict:
        """Crea el bloque animado de pensamiento de la IA."""
        return {"type": "thinking"}

    @classmethod
    def create_divider(cls) -> dict:
        """Crea una línea divisoria visual."""
        return {"type": "divider"}

    @classmethod
    def create_blockquote(cls, text: str | dict, credit: str | None = None) -> dict:
        """Crea un bloque de cita destacado."""
        rich_text = text if isinstance(text, dict) else {"text": text}
        block = {
            "type": "blockquote",
            "text": rich_text
        }
        if credit:
            block["credit"] = {"text": credit}
        return block

    # ── Conversor HTML -> RichText ──────────────────────────────────────────

    @classmethod
    def html_to_rich_text(cls, html_text: str) -> dict:
        """
        Parsea HTML básico y extrae el texto plano junto con las entidades RichText.
        Soporta <b>, <strong>, <i>, <em>, <code>, <pre>, <a href="...">.
        """
        if not html_text:
            return {"text": ""}

        # Sanitizar saltos de línea y tags
        tag_re = re.compile(
            r'<(b|strong|i|em|code|pre|a)(?:\s+href="([^"]+)")?>(.*?)</\1>',
            re.IGNORECASE | re.DOTALL
        )

        entities = []
        plain_text = ""
        last_idx = 0

        # Normalizar espaciado y saltos de línea de HTML a texto plano
        text_to_parse = html_text.strip()

        for match in tag_re.finditer(text_to_parse):
            start_text = text_to_parse[last_idx:match.start()]
            plain_text += start_text

            tag = match.group(1).lower()
            href = match.group(2)
            content = match.group(3)

            # Limpiar etiquetas HTML anidadas residuales en el contenido
            clean_content = re.sub(r'<[^>]+>', '', content)

            offset = len(plain_text)
            length = len(clean_content)

            plain_text += clean_content
            last_idx = match.end()

            # Determinar tipo de entidad de Telegram
            entity_type = None
            if tag in ("b", "strong"):
                entity_type = "bold"
            elif tag in ("i", "em"):
                entity_type = "italic"
            elif tag == "code":
                entity_type = "code"
            elif tag == "pre":
                entity_type = "preformatted"
            elif tag == "a" and href:
                entity_type = "text_link"

            if entity_type:
                ent = {"type": entity_type, "offset": offset, "length": length}
                if entity_type == "text_link":
                    ent["url"] = href
                entities.append(ent)

        plain_text += text_to_parse[last_idx:]
        # Remover cualquier etiqueta residual huérfana
        plain_text = re.sub(r'<[^>]+>', '', plain_text)

        # Reemplazar entidades de escape HTML comunes
        plain_text = (
            plain_text.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
        )

        rich_res = {"text": plain_text}
        if entities:
            rich_res["entities"] = entities

        return rich_res
