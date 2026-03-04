import asyncio
import logging
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from repositories.book_repository import book_repo
from repositories.upload_repository import upload_repo
from services.ai_service import AIService
from services.epub_service import enrich_metadata_from_epub
from services.hash_service import hash_service
from services.scanner.series_scanner import SeriesScanner
from services.settings_service import get_setting
from utils.metadata_utils import process_book_identity_comprehensive

logger = logging.getLogger(__name__)


class UploadService:
    """
    Servicio para gestionar el ciclo de vida de la subida de libros (EPUBs).
    Encapsula análisis, enriquecimiento con IA, validación de duplicados y persistencia.
    """

    def __init__(self):
        self.temp_dir = Path("/tmp/epub_uploads")
        self.temp_dir.mkdir(exist_ok=True)
        self.library_base = Path("/library")

    async def analyze_epub(self, epub_path: Path, original_filename: str, user_id: int) -> dict[str, Any] | None:
        """Analiza el EPUB, aplica IA si está activa y determina identidad."""
        try:
            if not await self._validate_epub_structure(epub_path):
                return None

            # 1. Extraer metadata básica del OPF y enriquecerla (lógica legacy)
            enriched_metadata = await enrich_metadata_from_epub(
                epub_bytes=str(epub_path),
                epub_url=f"file://{epub_path}",
                existing_meta={},
            )

            if not enriched_metadata:
                return None

            # 2. Mapear a formato interno de metadata
            metadata = self._map_enriched_to_internal(enriched_metadata, original_filename)

            # 3. Integración con IA (Gemini)
            bg_ai_enabled = get_setting("enable_background_ai_scan", "false").lower() == "true"
            if bg_ai_enabled:
                ai_data = await AIService.normalize_book_metadata(original_filename, metadata)
                if ai_data:
                    self._apply_ai_enrichment(metadata, ai_data)

            # 4. Lógica de Identidad (Hashes)
            identity = await self._determine_identity(epub_path, original_filename, metadata)

            # Actualizar metadata con identidad final
            metadata.update(
                {
                    "series": identity.get("series"),
                    "author": identity.get("author"),
                    "volume": identity.get("volume"),
                    "book_hash": identity.get("book_hash"),
                    "series_hash": identity.get("series_hash"),
                }
            )

            # 5. Verificar duplicados
            existing_book = await book_repo.get_by_hash(metadata["book_hash"])
            metadata["identity_match"] = {
                "exists": existing_book is not None,
                "path": existing_book.filepath if existing_book else None,
                "id": existing_book.id if existing_book else None,
            }

            # 6. Determinar destino inteligente
            metadata["suggested_path"] = await self._get_smart_destination(metadata, original_filename)

            # 7. Persistir registro temporal de upload
            await upload_repo.create_upload_record(
                {
                    "telegram_id": user_id,
                    "original_filename": original_filename,
                    "temp_filepath": str(epub_path),
                    "title": metadata["title"],
                    "series": metadata["series"],
                    "volume": self._parse_volume(metadata["volume"]),
                    "author": metadata["author"],
                    "book_type": metadata.get("book_type"),
                    "translator": metadata.get("translator"),
                    "layout_by": metadata.get("layout_by"),
                    "language": metadata.get("language", "es"),
                    "is_uncensored": metadata.get("is_uncensored", 0),
                    "color_mode": metadata.get("color_mode", "bw"),
                    "book_hash": metadata["book_hash"],
                    "series_hash": metadata["series_hash"],
                    "upload_metadata": metadata,
                    "identity_match": "True" if existing_book else "False",
                }
            )

            return metadata

        except Exception as e:
            logger.error(f"Error in UploadService.analyze_epub: {e}", exc_info=True)
            return None

    async def _validate_epub_structure(self, epub_path: Path) -> bool:
        """Valida que sea un ZIP/EPUB válido y contenga archivos necesarios."""
        if not epub_path.exists() or epub_path.stat().st_size == 0:
            return False
        try:
            with zipfile.ZipFile(epub_path, "r") as z:
                file_list = z.namelist()
                has_opf = any(f.lower().endswith(".opf") for f in file_list)
                has_container = any("container.xml" in f.lower() for f in file_list)
                return has_opf or has_container
        except zipfile.BadZipFile:
            return False

    def _map_enriched_to_internal(self, enriched: dict, original_filename: str) -> dict:
        """Mapea la metadata enriquecida al formato de control interno."""
        return {
            "title": enriched.get("titulo_volumen") or enriched.get("titulo_serie") or "Sin título",
            "author": enriched.get("autor")
            or (enriched.get("autores", ["Autor desconocido"])[0] if enriched.get("autores") else "Autor desconocido"),
            "description": enriched.get("sinopsis", ""),
            "language": enriched.get("idioma", "es"),
            "isbn": enriched.get("isbn", ""),
            "publisher": enriched.get("publisher", ""),
            "publish_date": enriched.get("fecha_publicacion", ""),
            "tags": ", ".join(enriched.get("generos", [])),
            "series": enriched.get("titulo_serie", ""),
            "volume": enriched.get("volume_index") or enriched.get("titulo_volumen", ""),
            "illustrator": enriched.get("ilustrador", ""),
            "translator": enriched.get("traductor", ""),
            "category": enriched.get("categoria", ""),
            "demography": enriched.get("demografia", []),
            "layout_by": enriched.get("maquetadores", [""])[0] if enriched.get("maquetadores") else "",
            "book_type": enriched.get("categoria", ""),
            "original_filename": original_filename,
        }

    def _apply_ai_enrichment(self, metadata: dict, ai_data: dict):
        """Aplica las mejoras detectadas por la IA."""
        if ai_data.get("series_name"):
            metadata["series"] = ai_data["series_name"]
        if ai_data.get("volume") is not None:
            metadata["volume"] = ai_data["volume"]
        if ai_data.get("group_full"):
            metadata["group"] = ai_data["group_full"]
        if ai_data.get("group_siglas"):
            metadata["group_siglas"] = ai_data["group_siglas"]
        if ai_data.get("suggested_filename"):
            metadata["ai_filename"] = ai_data["suggested_filename"]
        if ai_data.get("is_uncensored") is not None:
            metadata["is_uncensored"] = 1 if ai_data["is_uncensored"] else 0
        if ai_data.get("color_mode"):
            metadata["color_mode"] = ai_data["color_mode"]
        if ai_data.get("book_type"):
            metadata["book_type"] = ai_data["book_type"]
        if ai_data.get("genres"):
            metadata["tags"] = ", ".join(ai_data["genres"])
        if ai_data.get("demographics"):
            metadata["demography"] = ai_data["demographics"]
        if ai_data.get("cleaned_description"):
            metadata["description"] = ai_data["cleaned_description"]

    async def _determine_identity(self, epub_path: Path, original_filename: str, metadata: dict) -> dict:
        """Calcula hashes y normaliza identidad."""
        identity = process_book_identity_comprehensive(str(epub_path), original_filename)

        # Merge con datos de metadata (que pueden venir corregidos por IA)
        final_identity = {
            "series": metadata.get("series") or identity.get("series"),
            "author": metadata.get("author") or identity.get("author"),
            "book_type": metadata.get("book_type") or identity.get("book_type"),
            "volume": metadata.get("volume") if metadata.get("volume") is not None else identity.get("volume"),
            "translator": metadata.get("translator") or identity.get("translator"),
            "layout_by": metadata.get("layout_by") or identity.get("layout_by"),
            "language": metadata.get("language") or identity.get("language"),
            "is_uncensored": metadata.get("is_uncensored", 0),
            "color_mode": metadata.get("color_mode") or identity.get("color_mode", "bw"),
        }

        book_hash = hash_service.generate_book_hash(
            series=final_identity["series"],
            author=final_identity["author"],
            book_type=final_identity["book_type"],
            volume=final_identity["volume"],
            translator=final_identity["translator"],
            layout_by=final_identity["layout_by"],
            language=final_identity["language"],
            is_uncensored=final_identity["is_uncensored"],
            color_mode=final_identity["color_mode"],
        )

        series_hash = hash_service.generate_series_hash(
            series=final_identity["series"],
            author=final_identity["author"],
            book_type=final_identity["book_type"],
        )

        final_identity["book_hash"] = book_hash
        final_identity["series_hash"] = series_hash
        return final_identity

    async def _get_smart_destination(self, metadata: dict, original_filename: str) -> str:
        """Calcula la ruta de destino inteligente."""
        series_hash = metadata.get("series_hash")
        target_dir = None
        series_folder_name = None

        # Buscar si la serie ya tiene carpeta
        if series_hash:
            existing_book = await book_repo.get_one_by_attr("series_hash", series_hash)
            if existing_book and existing_book.filepath:
                rel_path = existing_book.filepath.replace("/library", "").lstrip("/")
                target_dir_rel = os.path.dirname(rel_path)
                if (self.library_base / target_dir_rel).exists():
                    target_dir = self.library_base / target_dir_rel
                    series_folder_name = target_dir_rel

        if not target_dir:
            author = self._clean_fs_name(metadata.get("author", "Autor desconocido"))
            series = metadata.get("series", "")
            tag = self._determine_novel_type_tag(metadata, original_filename)

            series_ok = re.sub(r"\s*\[(?:NL|NW)\]\s*$", "", series, flags=re.IGNORECASE) if series else ""
            series_clean = self._clean_fs_name(series_ok)
            series_folder_name = f"{series_clean} - {author} [{tag}]" if series_clean else f"{author} [{tag}]"
            target_dir = self.library_base / series_folder_name

        # Nombre de archivo
        if metadata.get("ai_filename"):
            filename = metadata["ai_filename"]
        else:
            filename = await self._generate_pattern_filename(target_dir, metadata, original_filename)

        return f"{series_folder_name}/{filename}"

    async def _generate_pattern_filename(self, target_dir: Path, metadata: dict, original_filename: str) -> str:
        """Genera nombre de archivo basado en el patrón de la carpeta o el estándar."""
        series = metadata.get("series", "")
        series_ok = re.sub(r"\s*\[(?:NL|NW)\]\s*$", "", series, flags=re.IGNORECASE) if series else ""

        volume = metadata.get("volume")
        vol_str = self._format_volume_str(volume)

        # Detectar grupo
        group = self._clean_fs_name(
            metadata.get("publisher")
            or (metadata.get("typesetters") or [""])[0]
            or metadata.get("translator")
            or "Unknown"
        )
        group = re.sub(r"https?://\S+", "", group).strip()

        # Fallback de nombre de serie
        base_series_name = series_ok

        # Si la carpeta existe, intentar imitar el patrón
        if target_dir.exists():
            files = [f for f in os.listdir(target_dir) if f.lower().endswith(".epub")]
            for f in files:
                if " - V" in f and "[" in f and "].epub" in f:
                    return f"{base_series_name} - V{vol_str} [{group}].epub"

        if base_series_name:
            return f"{base_series_name} - V{vol_str} [{group}].epub"

        clean_name = re.sub(r"\s*\[.*?\]\s*", "", original_filename.rsplit(".", 1)[0])
        return f"{clean_name}.epub"

    def _format_volume_str(self, volume: Any) -> str:
        if volume is None:
            return "00"
        try:
            v_float = float(volume)
            if v_float == int(v_float):
                return f"{int(v_float):02d}"
            parts = str(v_float).split(".")
            return f"{int(parts[0]):02d}.{parts[1]}"
        except Exception:
            return str(volume)

    def _clean_fs_name(self, name: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        return name[:100].strip()

    def _determine_novel_type_tag(self, metadata: dict, original_filename: str) -> str:
        fname_lower = original_filename.lower()
        if "[nl]" in fname_lower:
            return "NL"
        if "[nw]" in fname_lower:
            return "NW"

        # Lógica heurística simplificada
        indicators = {
            "NL": ["shinsengumi", "light novel", "shonen", "seinen"],
            "NW": ["novela web", "web novel", "wn", "syosetu"],
        }
        text_to_check = (
            f"{metadata.get('publisher', '')} {metadata.get('tags', '')} {metadata.get('description', '')}".lower()
        )

        for tag, words in indicators.items():
            if any(word in text_to_check for word in words):
                return tag
        return "NL"

    def _parse_volume(self, volume_str: Any) -> float | None:
        if not volume_str:
            return None
        try:
            match = re.search(r"(\d+(?:\.\d+)?)", str(volume_str))
            return float(match.group(1)) if match else None
        except Exception:
            return None

    async def finalize_upload(self, epub_path: Path, suggested_path: str, metadata: dict) -> bool:
        """Mueve el archivo a su ubicación final e indexa."""
        try:
            full_path = self.library_base / suggested_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(epub_path), str(full_path))

            # Escaneo proactivo
            from services.scanner_service import ScannerService

            scanner = ScannerService(os.getenv("LOCAL_LIBRARIES", "{}"))
            await asyncio.sleep(0.5)
            scan_result = await scanner.sync_path(str(full_path), force_scan=True)

            if scan_result and (scan_result.get("added") or scan_result.get("updated")):
                # Forzar actualización de campos específicos confirmados que el scanner podría no ver bien
                db_data = {
                    "book_type": metadata.get("book_type"),
                    "is_uncensored": metadata.get("is_uncensored", 0),
                    "color_mode": metadata.get("color_mode", "bw"),
                    "description": metadata.get("description"),
                }
                # Buscar libro por filepath y actualizar
                book = await book_repo.get_by_filepath(str(full_path))
                if book:
                    await book_repo.update(book.id, db_data)
                    # Sincronizar serie
                    from core.db_manager_pg import pg_manager

                    async with pg_manager.get_session() as session:
                        await SeriesScanner.sync_series_metadata(session, book.series_hash)
                return True
            return False
        except Exception as e:
            logger.error(f"Error in finalize_upload: {e}", exc_info=True)
            return False


upload_service = UploadService()
