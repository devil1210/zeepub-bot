# api/routes/library_routes.py

import logging
import os
from typing import Annotated, Any
from urllib.parse import urlparse

import aiofiles
import httpx
from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from api.deps import require_mini_app_access
from services.epub_service import extract_internal_title, parse_opf_from_epub
from utils.http_client import fetch_bytes
from utils.url_cache import get_url_from_hash

logger = logging.getLogger(__name__)


class LibraryRoutes:
    """
    Handle library-related endpoints: downloads, file serving.
    Single Responsibility: Library content delivery and file management.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api")

    def get_router(self) -> APIRouter:
        """Return the configured router."""
        return self.router

    async def short_download(self, url_hash: str):
        """
        Endpoint acortado para descargas usando hash SHA256.
        Garantiza compatibilidad 100% con URLs remotas y archivos locales.
        """
        try:
            logger.info(f"📥 Short download request: {url_hash}")

            # Get URL from hash
            source_url = get_url_from_hash(url_hash)
            if not source_url:
                logger.warning(f"❌ No URL found for hash: {url_hash}")
                return JSONResponse(content={"error": "URL no encontrada o expirada"}, status_code=404)

            # Extraer título legible de la URL o archivo de manera segura
            from urllib.parse import unquote, urlparse
            try:
                parsed = urlparse(source_url)
                title = unquote(parsed.path.split("/")[-1]).replace(".epub", "")
            except Exception:
                title = "libro"

            if not title:
                title = "libro"

            # Delegar la descarga/entrega al método público incluyendo el url_hash para Self-Healing
            return await self.public_download(url=source_url, title=title, url_hash=url_hash)

        except Exception as e:
            logger.error(f"❌ Error in short download resolver: {e}", exc_info=True)
            return JSONResponse(content={"error": "Error interno al procesar la descarga"}, status_code=500)

    async def _serve_local_file(self, filepath: str, title: str):
        """Helper para servir un archivo local como streaming de forma asíncrona."""
        async def iterfile_async():
            try:
                async with aiofiles.open(filepath, mode="rb") as f:
                    while chunk := await f.read(64 * 1024):
                        yield chunk
            except Exception as e:
                logger.error(f"❌ Error reading local file: {e}")
                return

        return StreamingResponse(
            content=iterfile_async(),
            media_type="application/epub+zip",
            headers={
                "Content-Disposition": f'attachment; filename="{title}.epub"',
                "Cache-Control": "public, max-age=31536000",
            },
        )

    async def public_download(
        self,
        url: str = Query(..., description="Source EPUB URL or Local Path"),
        title: str = Query("libro", description="Filename hint"),
        url_hash: str | None = None,
    ):
        """
        Endpoint público para descargas directas.
        Soporta auto-recuperación de paths físicos locales renombrados o movidos.
        """
        try:
            logger.info(f"📥 Public download request: {url}")

            # 1. Caso URL Remota
            if url.startswith(("http://", "https://")):
                data = await fetch_bytes(url)
                if not data:
                    return Response(content={"error": "No se pudo descargar el archivo"}, status_code=404)

                return StreamingResponse(
                    content=iter([data]),
                    media_type="application/epub+zip",
                    headers={
                        "Content-Disposition": f'attachment; filename="{title}.epub"',
                        "Cache-Control": "public, max-age=31536000",
                    },
                )

            # 2. Caso Archivo Local Existente
            elif os.path.exists(url) and os.path.isfile(url):
                return await self._serve_local_file(url, title)

            # 3. Caso Auto-Recuperación (Self-Healing) de Archivos Locales Reubicados/Renombrados
            else:
                logger.warning(f"Archivo local no encontrado en ruta original: {url}")
                logger.info("Iniciando proceso de Auto-Recuperacion Dinamica...")

                filename_to_find = os.path.basename(url)
                
                try:
                    from core.db_manager_pg import pg_manager
                    from models.library import Book
                    from sqlalchemy import select

                    async with pg_manager.get_session() as session:
                        stmt = select(Book.filepath).where(Book.filename == filename_to_find).limit(1)
                        result = await session.execute(stmt)
                        new_filepath = result.scalar_one_or_none()

                    if new_filepath and os.path.exists(new_filepath):
                        logger.info(f"Archivo auto-recuperado exitosamente: {new_filepath}")

                        # Actualizar url_mappings en segundo plano para optimizar futuras descargas
                        if url_hash:
                            try:
                                from utils.url_cache import _get_sa_engine
                                from sqlalchemy import Table, MetaData
                                engine = _get_sa_engine()
                                meta = MetaData()
                                url_mappings = Table("url_mappings", meta, autoload_with=engine)
                                with engine.begin() as conn:
                                    upd = url_mappings.update().where(url_mappings.c.hash == url_hash).values(url=new_filepath)
                                    conn.execute(upd)
                                logger.info(f"URL cache actualizada para hash '{url_hash}' con la nueva ruta.")
                            except Exception as update_err:
                                logger.error(f"Error actualizando la nueva ruta en cache: {update_err}")

                        return await self._serve_local_file(new_filepath, title)

                except Exception as recovery_err:
                    logger.error(f"Error durante el proceso de Auto-Recuperacion: {recovery_err}", exc_info=True)




                return Response(content={"error": "Archivo no encontrado o reubicado sin escaneo previo"}, status_code=404)

        except Exception as e:
            logger.error(f"❌ Error in public download: {e}", exc_info=True)
            return Response(content={"error": "Error al procesar descarga"}, status_code=500)


    async def download_book(
        self,
        request: Request,
        user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
    ):
        """
        Endpoint principal para descarga de libros.
        """
        try:
            logger.info(f"📥 Book download request from user: {user_data.get('user_id', 'unknown')}")

            # Parse request data
            data = await request.json()

            if not data or "url" not in data:
                return Response(content={"error": "URL no proporcionada"}, status_code=400)

            url = data["url"]

            # Handle different URL types
            if url.startswith(("http://", "https://")):
                # Remote URL download
                return await self._handle_remote_download(url, request)

            elif os.path.exists(url):
                # Local file download
                return await self._handle_local_download(url, request)

            else:
                return Response(content={"error": "Archivo no encontrado"}, status_code=404)

        except Exception as e:
            logger.error(f"❌ Error in book download: {e}")
            return Response(content={"error": "Error al descargar libro"}, status_code=500)

    async def _handle_remote_download(self, url: str, request: Request):
        """Handle remote URL download."""
        try:
            # Download file
            data = await fetch_bytes(url)
            if not data:
                return Response(content={"error": "No se pudo descargar el archivo remoto"}, status_code=404)

            # Extract title from URL or use default
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or "libro"

            # Stream response
            return StreamingResponse(
                content=iter([data]),
                media_type="application/epub+zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.epub"',
                    "Cache-Control": "public, max-age=31536000",
                },
            )

        except Exception as e:
            logger.error(f"❌ Error in remote download: {e}")
            return Response(content={"error": "Error al descargar archivo remoto"}, status_code=500)

    async def _handle_local_download(self, file_path: str, request: Request):
        """Handle local file download."""
        try:
            # Extract title from OPF if possible
            title = "libro"
            try:
                opf_data = parse_opf_from_epub(file_path)
                if opf_data:
                    title = extract_internal_title(opf_data)
            except Exception as e:
                logger.warning(f"Could not extract title from OPF: {e}")

            # Stream local file
            async def iterfile_async():
                try:
                    async with aiofiles.open(file_path, mode="rb") as f:
                        while chunk := await f.read(64 * 1024):
                            yield chunk
                except Exception as e:
                    logger.error(f"❌ Error reading local file: {e}")
                    return

            return StreamingResponse(
                content=iterfile_async(),
                media_type="application/epub+zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{title}.epub"',
                    "Cache-Control": "public, max-age=31536000",
                },
            )

        except Exception as e:
            logger.error(f"❌ Error in local download: {e}")
            return Response(content={"error": "Error al leer archivo local"}, status_code=500)

    def register_routes(self):
        """Register all library routes."""
        self.router.add_api_route(
            "/dl/{url_hash}",
            self.short_download,
            methods=["GET"],
            summary="Download by hash",
            description="Download EPUB using SHA256 hash",
        )

        self.router.add_api_route(
            "/public/dl",
            self.public_download,
            methods=["GET"],
            summary="Public download",
            description="Download EPUB from URL or local path",
        )

        self.router.add_api_route(
            "/download",
            self.download_book,
            methods=["POST"],
            summary="Download book",
            description="Main book download endpoint",
        )
