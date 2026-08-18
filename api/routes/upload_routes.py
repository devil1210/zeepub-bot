# api/routes/upload_routes.py
"""
ZeePub: Rutas HTTP REST para subida de EPUBs desde la Web App.
Expone los endpoints que el frontend consume directamente como multipart/form-data.
Los handlers de lógica de negocio viven en services/upload_service.py y
api/handlers/admin/library_handlers.py.
"""

import logging
import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from api.deps import require_mini_app_access

logger = logging.getLogger(__name__)

TEMP_UPLOAD_DIR = Path("/tmp/epub_uploads")
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class UploadRoutes:
    """
    Rutas REST de upload de EPUBs para la Web App.
    Single Responsibility: Recibir archivos y delegar al UploadService.
    """

    def __init__(self):
        self.router = APIRouter()

    def get_router(self) -> APIRouter:
        return self.router

    def register_routes(self):
        """Registra todos los endpoints de upload."""
        self.router.add_api_route(
            "/api/library/upload",
            self.upload_epub,
            methods=["POST"],
            summary="Subir EPUB individual",
        )
        self.router.add_api_route(
            "/api/library/upload/bulk",
            self.upload_epub_bulk,
            methods=["POST"],
            summary="Subir múltiples EPUBs",
        )
        self.router.add_api_route(
            "/api/library/upload/confirm",
            self.confirm_upload,
            methods=["POST"],
            summary="Confirmar upload individual",
        )
        self.router.add_api_route(
            "/api/library/upload/bulk/confirm",
            self.confirm_upload_bulk,
            methods=["POST"],
            summary="Confirmar upload masivo",
        )
        self.router.add_api_route(
            "/api/admin/upload-history",
            self.get_upload_history,
            methods=["GET"],
            summary="Historial de uploads",
        )

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _get_user_data(self, request: Request) -> dict[str, Any]:
        """Extrae datos del usuario validado por require_mini_app_access."""
        return getattr(request.state, "user_data", {})

    async def _save_temp_file(self, file: UploadFile) -> Path:
        """Guarda el UploadFile en disco y devuelve la ruta temporal."""
        if not file.filename or not file.filename.lower().endswith(".epub"):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos .epub")

        safe_name = Path(file.filename).name
        temp_path = TEMP_UPLOAD_DIR / f"{id(file)}_{safe_name}"
        try:
            with temp_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            logger.error(f"Error guardando archivo temporal: {e}")
            raise HTTPException(status_code=500, detail="Error al guardar el archivo")
        finally:
            await file.close()
        return temp_path

    # ──────────────────────────────────────────────
    # Endpoints
    # ──────────────────────────────────────────────

    async def upload_epub(
        self,
        request: Request,
        file: UploadFile = File(...),
        user_data: dict[str, Any] = Depends(require_mini_app_access),
    ):
        """
        Recibe un EPUB, lo guarda temporalmente, lo analiza con UploadService
        y retorna la metadata extraída + el upload_id para confirmar después.
        """
        from services.upload_service import upload_service

        user_id = user_data.get("telegram_id", 0) or user_data.get("user_id", 0)

        # Verificar permisos de upload
        can_upload = (
            user_data.get("role") in ("admin", "mod")
            or user_data.get("can_upload_epub")
            or user_data.get("canUploadEpub")
        )
        if not can_upload:
            raise HTTPException(status_code=403, detail="No tienes permiso para subir libros")

        temp_path = await self._save_temp_file(file)
        logger.info(f"📤 Upload recibido: {file.filename} | user_id={user_id}")

        try:
            metadata = await upload_service.analyze_epub(
                epub_path=temp_path,
                original_filename=file.filename,
                user_id=user_id,
            )
            if not metadata:
                raise HTTPException(status_code=422, detail="No se pudo extraer metadata del EPUB")
            return metadata
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error analizando EPUB: {e}", exc_info=True)
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail="Error al procesar el EPUB")

    async def upload_epub_bulk(
        self,
        request: Request,
        files: list[UploadFile] = File(...),
        user_data: dict[str, Any] = Depends(require_mini_app_access),
    ):
        """
        Recibe múltiples EPUBs y los analiza en paralelo.
        Retorna lista de resultados con metadata por archivo.
        """
        from services.upload_service import upload_service

        user_id = user_data.get("telegram_id", 0) or user_data.get("user_id", 0)

        can_upload = (
            user_data.get("role") in ("admin", "mod")
            or user_data.get("can_upload_epub")
            or user_data.get("canUploadEpub")
        )
        if not can_upload:
            raise HTTPException(status_code=403, detail="No tienes permiso para subir libros")

        results = []
        for file in files:
            try:
                temp_path = await self._save_temp_file(file)
                metadata = await upload_service.analyze_epub(
                    epub_path=temp_path,
                    original_filename=file.filename,
                    user_id=user_id,
                )
                if metadata:
                    results.append({"success": True, **metadata})
                else:
                    results.append({"success": False, "filename": file.filename, "error": "No se pudo extraer metadata"})
            except HTTPException as e:
                results.append({"success": False, "filename": file.filename, "error": e.detail})
            except Exception as e:
                logger.error(f"Error bulk upload {file.filename}: {e}", exc_info=True)
                results.append({"success": False, "filename": file.filename, "error": str(e)})
        return results

    async def confirm_upload(
        self,
        request: Request,
        user_data: dict[str, Any] = Depends(require_mini_app_access),
    ):
        """
        Confirma un upload individual: mueve el archivo al destino final
        (Nextcloud si está activo, o disco local) e indexa el libro.
        """
        from api.handlers.admin.library_handlers import handle_upload_confirm_internal

        data = await request.json()

        try:
            result = await handle_upload_confirm_internal(data, user_data)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error confirmando upload: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error al confirmar el upload")

    async def confirm_upload_bulk(
        self,
        request: Request,
        user_data: dict[str, Any] = Depends(require_mini_app_access),
    ):
        """
        Confirma múltiples uploads en bloque.
        """
        from api.handlers.admin.library_handlers import handle_admin_bulk_upload_confirm

        data = await request.json()

        try:
            result = await handle_admin_bulk_upload_confirm(data, user_data)
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error confirmando bulk upload: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error al confirmar el upload masivo")

    async def get_upload_history(
        self,
        request: Request,
        limit: int = 100,
        offset: int = 0,
        user_data: dict[str, Any] = Depends(require_mini_app_access),
    ):
        """
        Retorna el historial de uploads de EPUBs.
        Equivalente al handler handle_get_upload_history del miniapp.
        """
        from api.handlers.admin.library_handlers import handle_get_upload_history

        try:
            result = await handle_get_upload_history(
                {"limit": limit, "offset": offset}, user_data
            )
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo historial de uploads: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error al obtener el historial")


