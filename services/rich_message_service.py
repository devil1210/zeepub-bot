# services/rich_message_service.py
#
# Servicio para gestionar el renderizado y envío de Rich Messages (API 10.2).
# Single Responsibility: Proveer los builders de bloques y transporte HTTP directo.
#

import json
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
    async def send_rich_message(
        cls,
        chat_id: int | str,
        blocks: list[dict] | None = None,
        html: str | None = None,
        markdown: str | None = None,
        media: list[dict] | None = None,
        files: dict | None = None,
        **kwargs
    ) -> dict | None:
        """
        Envía un mensaje enriquecido al chat especificado usando POST directo.
        Soporta bloques estructurados, Rich HTML o Rich Markdown.
        Si se pasa el parámetro `files`, utiliza multipart/form-data de forma automática.
        """
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendRichMessage"
        
        rich_payload = {}
        if blocks is not None:
            rich_payload["blocks"] = blocks
        if html is not None:
            rich_payload["html"] = html
        if markdown is not None:
            rich_payload["markdown"] = markdown
        if media is not None:
            rich_payload["media"] = media

        payload = {
            "chat_id": chat_id,
            "rich_message": rich_payload,
            **kwargs
        }
        if "reply_markup" in payload:
            markup = payload["reply_markup"]
            if hasattr(markup, "to_dict"):
                payload["reply_markup"] = markup.to_dict()

        try:
            logger.info(f"[RichMessageService] Enviando rich message al chat {chat_id}")
            async with httpx.AsyncClient() as client:
                if files:
                    payload["rich_message"] = json.dumps(payload["rich_message"])
                    if "reply_markup" in payload and payload["reply_markup"] is not None:
                        payload["reply_markup"] = json.dumps(payload["reply_markup"])
                    
                    response = await client.post(url, data=payload, files=files, timeout=30.0)
                else:
                    response = await client.post(url, json=payload, timeout=30.0)
                
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"[RichMessageService] Error en sendRichMessage: {result}")
                return result
        except Exception as e:
            logger.error(f"[RichMessageService] Excepción de transporte en sendRichMessage: {e}", exc_info=True)
            return None

    @classmethod
    async def edit_rich_message(
        cls,
        chat_id: int | str,
        message_id: int | str,
        blocks: list[dict] | None = None,
        html: str | None = None,
        markdown: str | None = None,
        media: list[dict] | None = None,
        files: dict | None = None,
        **kwargs,
    ) -> dict | None:
        """
        Edita un Rich Message existente in-place usando el endpoint editMessageText
        con el payload estructurado de rich_message. (Telegram Bot API 10.1+)
        """
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/editMessageText"

        rich_payload = {}
        if blocks is not None:
            rich_payload["blocks"] = blocks
        if html is not None:
            rich_payload["html"] = html
        if markdown is not None:
            rich_payload["markdown"] = markdown
        if media is not None:
            rich_payload["media"] = media

        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "rich_message": rich_payload,
            **kwargs,
        }
        if "reply_markup" in payload:
            markup = payload["reply_markup"]
            if hasattr(markup, "to_dict"):
                payload["reply_markup"] = markup.to_dict()

        try:
            logger.info(
                f"[RichMessageService] Editando rich message in-place en chat {chat_id}, msg {message_id}"
            )
            async with httpx.AsyncClient() as client:
                if files:
                    payload["rich_message"] = json.dumps(payload["rich_message"])
                    if (
                        "reply_markup" in payload
                        and payload["reply_markup"] is not None
                    ):
                        payload["reply_markup"] = json.dumps(payload["reply_markup"])
                    response = await client.post(
                        url, data=payload, files=files, timeout=60.0
                    )
                else:
                    response = await client.post(url, json=payload, timeout=60.0)

                result = response.json()
                if not result.get("ok"):
                    logger.error(
                        f"[RichMessageService] Error en edit_rich_message: {result}"
                    )
                return result
        except Exception as e:
            logger.error(
                f"[RichMessageService] Excepción en edit_rich_message: {e}",
                exc_info=True,
            )
            return None

    @classmethod
    async def send_rich_message_draft(
        cls,
        chat_id: int | str,
        blocks: list[dict] | None = None,
        html: str | None = None,
        markdown: str | None = None,
        media: list[dict] | None = None,
        draft_id: str | None = None,
        files: dict | None = None,
        **kwargs
    ) -> dict | None:
        """
        Envía o actualiza un borrador enriquecido (AI Streaming) usando POST directo.
        """
        url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendRichMessageDraft"
        
        rich_payload = {}
        if blocks is not None:
            rich_payload["blocks"] = blocks
        if html is not None:
            rich_payload["html"] = html
        if markdown is not None:
            rich_payload["markdown"] = markdown
        if media is not None:
            rich_payload["media"] = media

        payload = {
            "chat_id": chat_id,
            "rich_message": rich_payload,
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
                if files:
                    payload["rich_message"] = json.dumps(payload["rich_message"])
                    if "reply_markup" in payload and payload["reply_markup"] is not None:
                        payload["reply_markup"] = json.dumps(payload["reply_markup"])
                    
                    response = await client.post(url, data=payload, files=files, timeout=30.0)
                else:
                    response = await client.post(url, json=payload, timeout=30.0)
                
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"[RichMessageService] Error en sendRichMessageDraft: {result}")
                return result
        except Exception as e:
            logger.error(f"[RichMessageService] Excepción de transporte en sendRichMessageDraft: {e}", exc_info=True)
            return None



    # ── Builders de Bloques ──────────────────────────────────────────────────

    @classmethod
    def create_paragraph(cls, text: str | dict) -> dict:
        """Crea un bloque de párrafo. Acepta una cadena de texto o un diccionario con text y entities."""
        if isinstance(text, dict):
            block = {
                "type": "paragraph",
                "text": text["text"]
            }
            if text.get("entities"):
                block["entities"] = text["entities"]
            return block
        else:
            text_str = str(text)
            if "<" in text_str and ">" in text_str:
                parsed = cls.html_to_rich_text(text_str)
                block = {
                    "type": "paragraph",
                    "text": parsed["text"]
                }
                if parsed.get("entities"):
                    block["entities"] = parsed["entities"]
                return block
            return {
                "type": "paragraph",
                "text": text_str
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
    def create_table(
        cls,
        headers: list[str],
        rows: list[list[str]],
        caption: str | None = None,
        is_compact: bool = True,
    ) -> dict:
        """
        Crea un bloque de tabla responsivo con soporte para is_compact (API 10.3).
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
            "rows": table_rows,
            "is_compact": is_compact,
        }
        if caption:
            table_block["caption"] = {"text": caption}
        return table_block

    @classmethod
    def create_details(cls, title: str, blocks: list[dict], is_open: bool = False) -> dict:
        """Crea un bloque colapsable de detalles."""
        return {
            "type": "details",
            "summary": title,
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
        paragraph_text = text if isinstance(text, (dict, list)) else str(text)
        block = {
            "type": "blockquote",
            "blocks": [
                {
                    "type": "paragraph",
                    "text": paragraph_text,
                }
            ],
        }
        if credit:
            block["credit"] = {"text": credit}
        return block

    @classmethod
    def create_document(
        cls,
        document_id: str,
        title: str | None = None,
        mime_type: str = "application/epub+zip",
    ) -> dict:
        """
        Crea un bloque de documento integrado en el Rich Message (Bot API 10.3).
        Permite adjuntar el archivo directamente dentro del cuerpo enriquecido.
        """
        doc_ref = (
            document_id
            if document_id.startswith(("http://", "https://", "tg://", "attach://"))
            else f"attach://{document_id}"
        )
        doc_block = {
            "type": "document",
            "document": doc_ref,
        }
        if title:
            doc_block["title"] = title
        if mime_type:
            doc_block["mime_type"] = mime_type
        return doc_block

    # ── Conversor HTML -> RichText ──────────────────────────────────────────

    @classmethod
    def html_to_rich_text(cls, html_text: str) -> dict:
        """
        Parsea HTML básico y extrae el texto plano junto con las entidades.
        Soporta <b>, <strong>, <i>, <em>, <code>, <pre>, <a href="...">.
        """
        if not html_text:
            return {"text": "", "entities": []}

        tag_pattern = r'<(b|strong|i|em|code|pre|a)(?:\s+href=["\']([^"\']+)["\'])?>(.*?)</\1>'
        tag_re = re.compile(tag_pattern, re.IGNORECASE | re.DOTALL)

        entities = []
        plain_text = ""
        last_idx = 0
        text_to_parse = html_text.strip()

        def clean_and_escape(text: str) -> str:
            # Remover etiquetas residuales huérfanas
            text = re.sub(r'<[^>]+>', '', text)
            return (
                text.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
            )

        for match in tag_re.finditer(text_to_parse):
            start_text = text_to_parse[last_idx:match.start()]
            plain_text += clean_and_escape(start_text)

            tag = match.group(1).lower()
            href = match.group(2)
            content = match.group(3)

            clean_content = clean_and_escape(content)
            offset = len(plain_text)
            length = len(clean_content)

            plain_text += clean_content
            last_idx = match.end()

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

        residual = text_to_parse[last_idx:]
        if residual:
            plain_text += clean_and_escape(residual)

        return {
            "text": plain_text,
            "entities": entities
        }
