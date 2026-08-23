import asyncio
import logging
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from sqlalchemy import select

from core.db_manager_pg import pg_manager
from models.library import LibrarySource
from repositories.book_repository import book_repo
from repositories.upload_repository import upload_repo
from services.ai_service import AIService
from services.epub_service import enrich_metadata_from_epub
from services.hash_service import hash_service
from services.scanner.series_scanner import SeriesScanner
from services.settings_service import get_setting
from utils.helpers import normalize_demographics_list
from utils.metadata_utils import process_book_identity_comprehensive

logger = logging.getLogger(__name__)


class UploadService:
    """
    Servicio para gestionar el ciclo de vida de la subida de libros (EPUBs).
    Encapsula análisis, enriquecimiento con IA, validación de duplicados y persistencia.
    """

    def __init__(self):
        self.temp_dir = Path("/tmp/epub_uploads")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._library_base_cache = None
        self._active_source_id = None  # Initialize _active_source_id

    async def _get_library_base(self) -> Path:
        """Obtiene la ruta base de la librería dinámicamente, validando existencia."""
        if self._library_base_cache:
            return self._library_base_cache

        try:
            async with pg_manager.get_session() as session:
                # Intentar obtener todas las fuentes y elegir la que exista físicamente
                stmt = select(LibrarySource)
                result = await session.execute(stmt)
                sources = result.scalars().all()

                # Priorizar fuentes que existan en el sistema de archivos actual
                for source in sources:
                    p = Path(source.path)
                    if p.exists():
                        logger.info(
                            f"Usando fuente de librería activa: {source.name} ({source.path})"
                        )
                        self._library_base_cache = p
                        self._active_source_id = source.id
                        return self._library_base_cache

                # Si ninguna existe (ej: VPS nuevo), usar la primera como fallback
                if sources:
                    source = sources[0]
                    self._library_base_cache = Path(source.path)
                    self._active_source_id = source.id
                    return self._library_base_cache

        except Exception as e:
            logger.warning(f"No se pudo obtener library_base de la DB: {e}")

        # Fallback a variable de entorno o default
        env_lib = os.getenv("LIBRARY_PATH") or os.getenv("LOCAL_LIBRARIES")
        if env_lib:
            try:
                # Si LOCAL_LIBRARIES es un JSON, intentamos parsearlo
                import json

                libs = json.loads(env_lib)
                if isinstance(libs, dict) and libs:
                    self._library_base_cache = Path(list(libs.values())[0])
                    self._active_source_id = 1
                    return self._library_base_cache
            except Exception:
                self._library_base_cache = Path(env_lib)
                self._active_source_id = 1
                return self._library_base_cache

        self._library_base_cache = Path("/library")
        self._active_source_id = 1
        return self._library_base_cache

    async def analyze_epub(
        self, epub_path: Path, original_filename: str, user_id: int
    ) -> dict[str, Any] | None:
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
                logger.warning(f"No se pudo extraer metadata de {original_filename}")
                return None

            # 2. Mapear a formato interno de metadata
            metadata = self._map_enriched_to_internal(
                enriched_metadata, original_filename
            )

            # 3. Integración con IA (Gemini) para normalización y título en español
            try:
                ai_data = await AIService.normalize_book_metadata(
                    original_filename, metadata
                )
                if ai_data:
                    self._apply_ai_enrichment(metadata, ai_data)
            except Exception as e:
                logger.warning(f"AI enrichment failed in analyze_epub: {e}")

            # 3.1 Fallback si no hay título en español: intentar resolver vía API
            if not metadata.get("series_spanish"):
                try:
                    from utils.metadata_utils import get_series_spanish_from_api

                    s_name = metadata.get("series") or metadata.get("title")
                    if s_name:
                        api_es = await get_series_spanish_from_api(
                            s_name, metadata.get("author")
                        )
                        if api_es:
                            metadata["series_spanish"] = api_es
                except Exception as e:
                    logger.debug(f"API spanish title lookup failed: {e}")

            # 4. Lógica de Identidad (Hashes)
            identity = await self._determine_identity(
                epub_path, original_filename, metadata
            )

            # Actualizar metadata con identidad final
            metadata.update(
                {
                    "uuid": identity.get("uuid"),
                    "series": identity.get("series"),
                    "author": identity.get("author"),
                    "volume": identity.get("volume"),
                    "book_hash": identity.get("book_hash"),
                    "series_hash": identity.get("series_hash"),
                }
            )

            # 5. Verificar duplicados
            # 5.1 Buscar por book_hash (identificador único con UUID o metadatos)
            existing_book = await book_repo.get_by_hash(metadata["book_hash"])

            # 5.2 Si no se encontró y hay UUID, buscar por hash de UUID directamente
            if not existing_book and metadata.get("uuid"):
                uuid_hash = hash_service.generate_book_hash(uuid=metadata["uuid"])
                existing_book = await book_repo.get_by_hash(uuid_hash)

            # 5.3 Si no se encontró por hash exacto, verificar si el volumen ya existe en la serie
            if not existing_book and metadata.get("volume") is not None:
                vol_parsed = self._parse_volume(metadata["volume"])
                if vol_parsed is not None:
                    # Buscar por series_hash
                    if metadata.get("series_hash"):
                        existing_book = await book_repo.get_by_series_and_volume(
                            metadata["series_hash"], vol_parsed
                        )
                    # Si no, buscar la serie por título / alias
                    if not existing_book:
                        from repositories.series_repository import series_repo

                        s_query = metadata.get("series") or metadata.get("title")
                        if s_query:
                            matched_series = await series_repo.find_by_title_or_alias(s_query)
                            if matched_series:
                                existing_book = await book_repo.get_by_series_and_volume(
                                    matched_series.id, vol_parsed
                                )

            if existing_book:
                metadata["identity_match"] = {
                    "exists": True,
                    "path": existing_book.filepath,
                    "id": existing_book.id,
                    "series": existing_book.series_info.name if existing_book.series_info else metadata.get("series"),
                    "volume": existing_book.volume,
                }
            else:
                metadata["identity_match"] = None

            # 6. Determinar destino inteligente
            metadata["suggested_path"] = await self._get_smart_destination(
                metadata, original_filename
            )

            # 7. Persistir registro temporal de upload y obtener ID
            record = await upload_repo.create_upload_record(
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
                    "processed": False,
                }
            )

            metadata["upload_id"] = record.id
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

    @staticmethod
    def _parse_volume(val: Any) -> float | None:
        """Parsea un número de volumen a float de forma robusta."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        import re

        try:
            match = re.search(r"(\d+(?:\.\d+)?)", str(val))
            if match:
                return float(match.group(1))
        except Exception:
            pass
        return None

    def _map_enriched_to_internal(self, enriched: dict, original_filename: str) -> dict:
        """Mapea la metadata enriquecida al formato de control interno."""
        return {
            "title": enriched.get("titulo_volumen")
            or enriched.get("titulo_serie")
            or "Sin título",
            "author": enriched.get("autor")
            or (
                enriched.get("autores", ["Autor desconocido"])[0]
                if enriched.get("autores")
                else "Autor desconocido"
            ),
            "description": enriched.get("sinopsis", ""),
            "language": enriched.get("idioma", "es"),
            "isbn": enriched.get("isbn", ""),
            "asin": enriched.get("asin", ""),
            "uuid": enriched.get("uuid"),
            "publisher": enriched.get("publisher", ""),
            "publish_date": enriched.get("fecha_publicacion", ""),
            "tags": ", ".join(enriched.get("generos", [])),
            "series": enriched.get("titulo_serie", ""),
            "volume": enriched.get("volume_index")
            or enriched.get("titulo_volumen", ""),
            "illustrator": enriched.get("ilustrador", ""),
            "translator": enriched.get("traductor", ""),
            "category": enriched.get("categoria", ""),
            "demography": normalize_demographics_list(enriched.get("demografia", [])),
            "layout_by": ", ".join(enriched.get("maquetadores", []))
            if enriched.get("maquetadores")
            else "",
            "book_type": enriched.get("categoria", ""),
            "original_filename": original_filename,
        }

    def _apply_ai_enrichment(self, metadata: dict, ai_data: dict):
        """Aplica las mejoras detectadas por la IA."""
        if ai_data.get("series_name"):
            metadata["series"] = ai_data["series_name"]
        if ai_data.get("series_spanish"):
            metadata["series_spanish"] = ai_data["series_spanish"]
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
            metadata["demography"] = normalize_demographics_list(
                ai_data["demographics"]
            )
        if ai_data.get("cleaned_description"):
            metadata["description"] = ai_data["cleaned_description"]

    async def _determine_identity(
        self, epub_path: Path, original_filename: str, metadata: dict
    ) -> dict:
        """Calcula hashes y normaliza identidad."""
        identity = process_book_identity_comprehensive(
            str(epub_path), original_filename=original_filename
        )

        # Merge con datos de metadata (que pueden venir corregidos por IA)
        final_identity = {
            "uuid": metadata.get("uuid") or identity.get("uuid"),
            "series": metadata.get("series") or identity.get("series"),
            "author": metadata.get("author") or identity.get("author"),
            "book_type": metadata.get("book_type") or identity.get("book_type"),
            "volume": metadata.get("volume")
            if metadata.get("volume") is not None
            else identity.get("volume"),
            "translator": metadata.get("translator") or identity.get("translator"),
            "layout_by": metadata.get("layout_by") or identity.get("layout_by"),
            "language": metadata.get("language") or identity.get("language"),
            "is_uncensored": metadata.get("is_uncensored", 0),
            "color_mode": metadata.get("color_mode")
            or identity.get("color_mode", "bw"),
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
            uuid=final_identity.get("uuid"),
        )

        series_hash = hash_service.generate_series_hash(
            series=final_identity["series"],
            author=final_identity["author"],
            book_type=final_identity["book_type"],
        )

        final_identity["book_hash"] = book_hash
        final_identity["series_hash"] = series_hash
        return final_identity

    async def _get_smart_destination(
        self, metadata: dict, original_filename: str
    ) -> str:
        """
        Calcula la ruta de destino inteligente.
        - Si la serie ya existe en la biblioteca, utiliza la MISMA carpeta y formato exacto existente.
        - El nombre del archivo se genera SIEMPRE en ESPAÑOL: {Título Español} - V{XX} [{Grupo}].epub
        """
        library_base = await self._get_library_base()
        lib_base_str = str(library_base).replace("\\", "/")

        target_dir = None
        series_folder_name = None
        existing_series_book = None
        matched_series = None

        # 1. Buscar si la serie ya existe en la base de datos
        try:
            from repositories.series_repository import series_repo

            # A) Buscar por series_hash / series_id
            series_hash = metadata.get("series_hash")
            if series_hash:
                existing_series_book = await book_repo.get_one_by_attr(
                    "series_hash", series_hash
                )
                if not existing_series_book:
                    existing_series_book = await book_repo.get_one_by_attr(
                        "series_id", series_hash
                    )
                if not existing_series_book:
                    matched_series = await series_repo.get_by_id(series_hash)

            # B) Buscar por título o alias de la serie
            if not existing_series_book and not matched_series:
                s_query = metadata.get("series") or metadata.get("title")
                if s_query:
                    matched_series = await series_repo.find_by_title_or_alias(s_query)

            # C) Buscar por título en español
            if not existing_series_book and not matched_series and metadata.get("series_spanish"):
                matched_series = await series_repo.find_by_title_or_alias(
                    metadata["series_spanish"]
                )

            # Si encontramos la serie pero no el libro individual, buscar cualquier libro de esa serie
            if matched_series and not existing_series_book:
                existing_series_book = await book_repo.get_one_by_attr(
                    "series_id", matched_series.id
                )
                if not existing_series_book:
                    existing_series_book = await book_repo.get_one_by_attr(
                        "series_hash", matched_series.id
                    )
        except Exception as e:
            logger.debug(f"DB lookup in _get_smart_destination omitted or failed: {e}")

        # 2. Si la serie YA EXISTE en la biblioteca:
        # Usar la carpeta EXACTA donde residen los volúmenes de esa serie
        if existing_series_book and existing_series_book.filepath:
            filepath_norm = existing_series_book.filepath.replace("\\", "/")
            rel_path = filepath_norm.replace(lib_base_str, "").lstrip("/")
            target_dir_rel = os.path.dirname(rel_path)
            if target_dir_rel:
                series_folder_name = target_dir_rel
                check_path = library_base / target_dir_rel
                if check_path.exists():
                    target_dir = check_path

            # Sincronizar nombres si existen en DB
            if getattr(existing_series_book, "series_info", None):
                if existing_series_book.series_info.name_spanish:
                    metadata["series_spanish"] = existing_series_book.series_info.name_spanish
                if existing_series_book.series_info.name:
                    metadata["series"] = existing_series_book.series_info.name

        elif matched_series:
            if matched_series.name_spanish:
                metadata["series_spanish"] = matched_series.name_spanish
            if matched_series.name:
                metadata["series"] = matched_series.name

        # 3. Si la serie NO existe en la biblioteca, generar nombre de carpeta estándar:
        # {Series Name} - {Author} [{Tag}]
        if not series_folder_name:
            author = self._clean_fs_name(metadata.get("author", "Autor desconocido"))
            series = metadata.get("series", "")
            tag = self._determine_novel_type_tag(metadata, original_filename)

            series_ok = (
                re.sub(r"\s*\[(?:NL|NW)\]\s*$", "", series, flags=re.IGNORECASE)
                if series
                else ""
            )
            series_clean = self._clean_fs_name(series_ok)
            series_folder_name = (
                f"{series_clean} - {author} [{tag}]"
                if series_clean
                else f"{author} [{tag}]"
            )
            target_dir = library_base / series_folder_name

        # 4. Generar nombre de archivo SIEMPRE en español
        filename = await self._generate_pattern_filename(
            target_dir, metadata, original_filename, existing_series_book
        )

        from utils.string_utils import sanitize_fs_path

        return sanitize_fs_path(f"{series_folder_name}/{filename}")

    async def _generate_pattern_filename(
        self,
        target_dir: Path | None,
        metadata: dict,
        original_filename: str,
        existing_book: Any = None,
    ) -> str:
        """
        Genera el nombre de archivo SIEMPRE en español respetando el patrón estándar:
        {Título en Español} - V{Volumen} [{Grupo}].epub
        Si la serie ya existe, imita exactamente el formato y nombre en español usado previamente.
        """
        from utils.string_utils import sanitize_fs_segment

        # 1. Determinar el título en ESPAÑOL
        spanish_title = (
            metadata.get("series_spanish")
            or metadata.get("spanish_title")
            or (
                existing_book.series_info.name_spanish
                if existing_book
                and getattr(existing_book, "series_info", None)
                and existing_book.series_info.name_spanish
                else None
            )
            or (
                existing_book.title
                if existing_book and getattr(existing_book, "title", None)
                else None
            )
            or (
                metadata.get("title")
                if metadata.get("title") and not metadata.get("title").endswith(".epub")
                else None
            )
            or metadata.get("series")
            or "Libro"
        )

        # Limpiar tags tipo [NL], [NW], volúmenes o extensiones residuales del título español
        spanish_title_clean = self._clean_series_base_title(str(spanish_title))

        # 2. Formatear volumen
        volume = metadata.get("volume")
        vol_str = self._format_volume_str(volume)

        # 3. Detectar grupo / siglas
        group = (
            metadata.get("group_siglas")
            or metadata.get("group")
            or metadata.get("publisher")
            or (metadata.get("typesetters") or [""])[0]
            or metadata.get("translator")
            or ""
        )
        group = re.sub(r"https?://\S+", "", str(group)).strip()
        group = self._clean_fs_name(group)
        if not group or group in ("?", "Unknown"):
            group = ""

        # 4. Si la carpeta existe en disco, verificar el patrón de los archivos existentes
        if target_dir and target_dir.exists():
            try:
                files = [
                    f for f in os.listdir(target_dir) if f.lower().endswith(".epub")
                ]
                for f in files:
                    if " - V" in f and "[" in f and "].epub" in f:
                        base_match = re.match(r"^(.*?)\s*-\s*V\d+", f, flags=re.IGNORECASE)
                        if base_match:
                            existing_base = base_match.group(1).strip()
                            if existing_base:
                                grp_to_use = group or "Unknown"
                                fn = f"{existing_base} - V{vol_str} [{grp_to_use}].epub"
                                return sanitize_fs_segment(fn)
            except Exception:
                pass

        # 5. Si la IA proporcionó un ai_filename en español y no hay conflicto
        if metadata.get("ai_filename"):
            ai_fn = self._clean_fs_name(metadata["ai_filename"])
            if ai_fn.lower().endswith(".epub"):
                return sanitize_fs_segment(ai_fn)

        # 6. Construcción estándar en español
        base_name = spanish_title_clean or "Libro"
        if group:
            fn = f"{base_name} - V{vol_str} [{group}].epub"
        else:
            fn = f"{base_name} - V{vol_str}.epub"

        return sanitize_fs_segment(fn)

    def _clean_series_base_title(self, raw_title: str) -> str:
        """Limpia un título eliminando tags de formato, grupos, sufijos de volumen y extensiones."""
        if not raw_title:
            return ""
        t = re.sub(r"\.epub$", "", str(raw_title), flags=re.IGNORECASE).strip()
        # Eliminar tags [NL], [NW], [Color], [SC], [Manga]
        t = re.sub(r"\s*\[(?:NL|NW|Color|SC|Manga)\]\s*", " ", t, flags=re.IGNORECASE)
        # Eliminar tags de grupo al final o si están entre corchetes
        t = re.sub(r"\s*\[.*?\]\s*", " ", t)
        # Eliminar subtítulos o eslóganes entre virgulillas tipo ~A combat maniac's ascension~
        t = re.sub(r"\s*[~～].*?[~～]\s*", " ", t)
        # Eliminar sufijos de volumen tipo "- Volumen 12", "- Tomo 12", "- Vol. 12", "- V12", "Volumen 12", "Tomo 12"
        t = re.sub(
            r"\s*-\s*(?:Volumen|Volume|Tomo|Vol\.?|V)\s*\d+(?:\.\d+)?.*$",
            "",
            t,
            flags=re.IGNORECASE,
        )
        t = re.sub(
            r"\s+(?:Volumen|Volume|Tomo|Vol\.?|V)\s*\d+(?:\.\d+)?.*$",
            "",
            t,
            flags=re.IGNORECASE,
        )
        # Eliminar sufijos numéricos tipo "- 12"
        t = re.sub(r"\s*-\s*\d+(?:\.\d+)?\s*$", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        return self._clean_fs_name(t)

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
        """Sanitiza nombres de archivos o carpetas con compatibilidad universal para todos los SO y Nextcloud."""
        from utils.string_utils import sanitize_fs_segment

        return sanitize_fs_segment(name)

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
        text_to_check = f"{metadata.get('publisher', '')} {metadata.get('tags', '')} {metadata.get('description', '')}".lower()

        for tag, words in indicators.items():
            if any(word in text_to_check for word in words):
                return tag
        return "NL"

    async def finalize_upload(
        self, epub_path: Path, suggested_path: str, metadata: dict
    ) -> bool:
        """Mueve el archivo a su ubicación final e indexa."""
        try:
            from utils.string_utils import sanitize_fs_path

            suggested_path = sanitize_fs_path(suggested_path)

            logger.info(
                f"Finalizando upload: sugiera path '{suggested_path}' para {epub_path.name}"
            )

            # Desviar a Nextcloud si las credenciales están configuradas
            from services.nextcloud_service import nextcloud_service

            if nextcloud_service.is_active:
                logger.info(
                    "☁️ Nextcloud detectado activo. Desviando la subida directamente a Nextcloud..."
                )
                upload_success = await nextcloud_service.upload_file(
                    epub_path, suggested_path
                )
                if upload_success:
                    # Borrar archivo temporal
                    if epub_path.exists():
                        try:
                            epub_path.unlink()
                        except Exception as unlink_err:
                            logger.warning(
                                f"No se pudo borrar el archivo temporal {epub_path}: {unlink_err}"
                            )

                    # Limpieza de registro temporal de upload_books en DB
                    upload_id = metadata.get("upload_id")
                    if upload_id:
                        try:
                            await upload_repo.delete_upload_record(int(upload_id))
                            logger.info(
                                f"Registro temporal de upload {upload_id} eliminado."
                            )
                        except Exception as e:
                            logger.warning(
                                f"No se pudo eliminar el registro temporal {upload_id}: {e}"
                            )

                    logger.info(
                        f"✅ Finalización de upload exitosa vía Nextcloud: {suggested_path}"
                    )
                    return True
                else:
                    logger.error("❌ Fallo subiendo el libro a Nextcloud.")
                    return False

            library_base = await self._get_library_base()
            source_id = getattr(self, "_active_source_id", 1)

            full_path = library_base / suggested_path

            # Asegurar que el directorio existe
            try:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(
                    f"No se pudo crear el directorio de destino {full_path.parent}: {e}"
                )
                return False

            logger.info(f"Moviendo {epub_path} -> {full_path}")

            # Mover con robustez ante fallos de cross-device
            if not epub_path.exists():
                logger.error(f"Archivo temporal no encontrado: {epub_path}")
                # Si el archivo no existe pero el libro ya está en la DB, quizás ya se movió exitosamente antes
                target_file_path = str(full_path).replace("\\", "/")
                existing = await book_repo.get_by_filepath(target_file_path)
                if existing:
                    logger.info(
                        "El libro ya existe en la ubicación final, marcando como éxito."
                    )
                    return True
                return False

            try:
                shutil.move(str(epub_path), str(full_path))
            except OSError as e:
                logger.warning(f"shutil.move falló, intentando copy+unlink: {e}")
                try:
                    shutil.copy2(str(epub_path), str(full_path))
                    os.unlink(str(epub_path))
                except Exception as e2:
                    logger.error(f"Fallo crítico moviendo archivo: {e2}")
                    return False

            # Escaneo proactivo
            from services.scanner_service import ScannerService

            scanner = ScannerService()
            await asyncio.sleep(0.5)

            # Normalizar path para el scanner
            target_file_path = str(full_path).replace("\\", "/")

            # IMPORTANTE: Pasar el source_id detectado
            try:
                scan_result = await scanner.sync_path(
                    target_file_path, source_id=source_id, force_scan=True
                )
                logger.info(f"Scan result para {target_file_path}: {scan_result}")
            except Exception as scan_err:
                logger.warning(
                    f"Error en scanner.sync_path (archivo ya fue movido): {scan_err}"
                )
                scan_result = None

            # El archivo ya fue movido exitosamente al disco.
            # Devolvemos True independientemente del resultado del scanner
            # (consistente con comportamiento en db23d1e: el scanner indexará en el próximo ciclo).
            book = await book_repo.get_by_filepath(target_file_path)

            if book:
                # Actualizar campos específicos confirmados
                db_data = {
                    "book_type": metadata.get("book_type"),
                    "is_uncensored": 1
                    if metadata.get("is_uncensored") in (1, True, "True")
                    else 0,
                    "color_mode": metadata.get("color_mode", "bw"),
                    "description": metadata.get("description"),
                }
                try:
                    await book_repo.update(book.id, db_data)
                except Exception as upd_err:
                    logger.warning(
                        f"No se pudo actualizar metadata post-scan: {upd_err}"
                    )

                # Sincronizar serie
                try:
                    async with pg_manager.get_session() as session:
                        await SeriesScanner.sync_series_metadata(
                            session, book.series_hash
                        )
                except Exception as ser_err:
                    logger.warning(f"No se pudo sincronizar serie: {ser_err}")
            else:
                logger.info(
                    f"Libro aún no indexado en DB (se indexará en próximo escaneo): {target_file_path}"
                )

            # LIMPIEZA DE UPLOAD_BOOKS
            upload_id = metadata.get("upload_id")
            if upload_id:
                try:
                    await upload_repo.delete_upload_record(int(upload_id))
                    logger.info(f"Registro temporal de upload {upload_id} eliminado.")
                except Exception as e:
                    logger.warning(
                        f"No se pudo eliminar el registro temporal {upload_id}: {e}"
                    )

            # Sincronización automática a la nube tras upload
            from services.sync_service import SyncService

            SyncService.trigger_auto_sync()

            logger.info(f"✅ finalize_upload exitoso: {target_file_path}")
            return True

        except Exception as e:
            logger.error(f"Error in finalize_upload: {e}", exc_info=True)
            return False


upload_service = UploadService()
