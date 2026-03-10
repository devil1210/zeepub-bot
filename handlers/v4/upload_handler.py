"""
handlers/v4/upload_handler.py
-------------------------------
UploadHandlerV4: Pipeline completo de ingesta de EPUBs vía Telegram.

Flujo:
  1. Usuario envía un archivo .epub al bot
  2. Telegram descarga el archivo a una carpeta temporal
  3. UploadHandler extrae los metadatos internos del EPUB (sin deps pesadas)
  4. CEOAgent.analyze_book → MetadataSwarm → BookProposal de Gemini
  5. LibraryService / BookRepository persiste el libro con los metadatos normalizados
  6. Se notifica al usuario con un resumen de lo procesado

Nota: La extracción de metadatos usa zipfile + xml.etree (stdlib pura)
para evitar dependencias pesadas. EbookLib se puede usar si está disponible.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from telegram import Document, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from services.v4.ai.ceo_agent import CEOAgent
from services.v4.library_service import LibraryService
from services.v4.storage_service import StorageService

from .base_handler import BaseHandlerV4

logger = logging.getLogger(__name__)

# Namespace OPF (EPUB 2/3)
_OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class UploadHandlerV4(BaseHandlerV4):
    """
    Procesa EPUBs enviados directamente al bot como documentos.
    También acepta el comando /upload si se reenvía un archivo.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ceo = CEOAgent()
        self.library_svc = LibraryService()
        self.storage_svc = StorageService()

    # ------------------------------------------------------------------ #
    #  Entry point: documento recibido                                     #
    # ------------------------------------------------------------------ #

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Procesa un archivo .epub enviado como documento."""
        doc: Document | None = update.message.document if update.message else None
        if not doc:
            return

        # Solo EPUBs
        if not doc.file_name or not doc.file_name.lower().endswith(".epub"):
            await self.reply(
                update,
                "⚠️ Solo acepto archivos <b>.epub</b>. Envíame un EPUB para indexarlo.",
            )
            return

        await self.ensure_user(update)
        uid = update.effective_user.id
        privs = await self.get_privileges(uid)

        if not privs.get("is_admin", False):
            await self.reply(update, "🔒 Solo administradores pueden subir libros.")
            return

        status_msg = await update.effective_message.reply_text(
            f"📥 <b>Recibiendo:</b> <code>{doc.file_name}</code>\n⏳ Procesando con IA...",
            parse_mode=ParseMode.HTML,
        )

        try:
            result = await self._ingest_epub(doc, context)
            await status_msg.edit_text(result, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"[UPLOAD] Error inesperado: {e}", exc_info=True)
            await status_msg.edit_text(
                f"❌ <b>Error interno al procesar el archivo.</b>\n<code>{type(e).__name__}: {e}</code>",
                parse_mode=ParseMode.HTML,
            )

    # ------------------------------------------------------------------ #
    #  Core ingesta                                                        #
    # ------------------------------------------------------------------ #

    async def _ingest_epub(self, doc: Document, context: ContextTypes.DEFAULT_TYPE) -> str:
        """
        Descarga, analiza con AI y persiste el EPUB.
        Devuelve el texto del mensaje de confirmación.
        """
        from config.config_settings import config

        library_path = Path(getattr(config, "LIBRARY_PATH", "/library"))

        # 1. Descargar el archivo EPUB vía Telegram
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / doc.file_name
            tg_file = await context.bot.get_file(doc.file_id)
            await tg_file.download_to_drive(str(tmp_path))

            logger.info(f"[UPLOAD] Descargado: {tmp_path} ({tmp_path.stat().st_size:,} bytes)")

            # 2. Extraer metadatos internos del EPUB (stdlib pura)
            raw_meta = await asyncio.to_thread(self._extract_epub_meta, tmp_path)

            # 3. Llamar al CEOAgent → MetadataSwarm → Gemini
            ceo_result = await self.ceo.execute_task(
                "analyze_book",
                {
                    "filename": doc.file_name,
                    "raw_metadata": raw_meta,
                    "title": raw_meta.get("title"),
                    "author": raw_meta.get("creator"),
                },
            )

            proposal_dict: dict = ceo_result.get("proposal", {})
            series_english: str = proposal_dict.get("series_english") or raw_meta.get("title", doc.file_name)
            series_spanish: str = proposal_dict.get("series_spanish") or series_english
            volume: float = float(proposal_dict.get("volume") or 0.0)
            confidence: float = float(proposal_dict.get("confidence") or 0.0)
            suggested_fn: str = proposal_dict.get("suggested_filename") or doc.file_name

            # 4. Mover el archivo al directorio de la biblioteca
            dest_path = library_path / _sanitize_dirname(series_spanish) / suggested_fn
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(self._move_file, tmp_path, dest_path)

            # 5. Persistir en la BD a través de LibraryService
            book_data = {
                "title": proposed_title(series_spanish, volume),
                "filepath": str(dest_path),
                "filename": suggested_fn,
                "file_size": doc.file_size or dest_path.stat().st_size,
                "volume": volume,
                "language": raw_meta.get("language", "es"),
                "series_name": series_spanish,
                "series_english": series_english,
                "book_type": proposal_dict.get("book_type", "novel"),
                "genres": proposal_dict.get("genres") or [],
                "description": proposal_dict.get("description") or raw_meta.get("description", ""),
            }

            await self.library_svc.ingest_book(book_data)

            # 6. Mensaje de confirmación rico
            return self._build_confirmation(
                original_name=doc.file_name,
                series_spanish=series_spanish,
                series_english=series_english,
                volume=volume,
                suggested_fn=suggested_fn,
                genres=proposal_dict.get("genres") or [],
                confidence=confidence,
                dest_path=dest_path,
            )

    # ------------------------------------------------------------------ #
    #  Extracción de metadatos EPUB (stdlib pura)                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_epub_meta(epub_path: Path) -> dict[str, Any]:
        """
        Lee el OPF del EPUB y extrae título, autor, publisher, idioma, descripción.
        Usa zipfile + xml.etree (sin dependencias).
        """
        meta: dict[str, Any] = {}
        try:
            with zipfile.ZipFile(epub_path, "r") as z:
                # Leer container.xml para encontrar el OPF
                container_xml = z.read("META-INF/container.xml").decode("utf-8", errors="replace")
                root = ET.fromstring(container_xml)
                opf_path = root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
                if opf_path is None:
                    return meta

                opf_full_path = opf_path.attrib.get("full-path", "")
                opf_xml = z.read(opf_full_path).decode("utf-8", errors="replace")

                opf_root = ET.fromstring(opf_xml)

                def _get(tag: str) -> str | None:
                    el = opf_root.find(f".//dc:{tag}", _OPF_NS)
                    return el.text.strip() if el is not None and el.text else None

                meta["title"] = _get("title")
                meta["creator"] = _get("creator")
                meta["publisher"] = _get("publisher")
                meta["language"] = _get("language")
                meta["description"] = _get("description")
                meta["date"] = _get("date")
                meta["subject"] = _get("subject")

        except Exception as e:
            logger.warning(f"[UPLOAD] No se pudo leer OPF: {e}")

        return {k: v for k, v in meta.items() if v}

    @staticmethod
    def _move_file(src: Path, dst: Path) -> None:
        import shutil

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    # ------------------------------------------------------------------ #
    #  Mensaje de confirmación                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_confirmation(
        original_name: str,
        series_spanish: str,
        series_english: str,
        volume: float,
        suggested_fn: str,
        genres: list[str],
        confidence: float,
        dest_path: Path,
    ) -> str:
        vol_str = "Único" if volume == 0 else f"{volume:g}"
        genre_str = " • ".join(genres[:5]) if genres else "N/D"
        conf_bar = "🟢" if confidence > 0.85 else "🟡" if confidence > 0.6 else "🔴"

        return (
            f"✅ <b>EPUB indexado correctamente</b>\n\n"
            f"📚 <b>Serie (ES):</b> {series_spanish}\n"
            f"🌍 <b>Serie (EN):</b> {series_english}\n"
            f"📖 <b>Volumen:</b> {vol_str}\n"
            f"🏷️ <b>Géneros:</b> {genre_str}\n\n"
            f"📁 <code>{suggested_fn}</code>\n"
            f"{conf_bar} <b>Confianza IA:</b> {confidence:.0%}\n\n"
            f"<i>Archivo original: {original_name}</i>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de módulo
# ─────────────────────────────────────────────────────────────────────────────


def _sanitize_dirname(name: str) -> str:
    """Elimina caracteres inválidos para usar como nombre de directorio."""
    import re

    return re.sub(r'[\\/:*?"<>|]', "-", name).strip(" .")


def proposed_title(series: str, volume: float) -> str:
    if volume == 0:
        return f"{series} — Volumen Único"
    return f"{series} — Vol. {volume:g}"
