import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

from api.deps import (
    require_admin,
    require_mini_app_access,
    get_current_user_data,
)

router = APIRouter(tags=["miniapp"])
logger = logging.getLogger(__name__)

# --- Modelos Pydantic ---


class AccessCheckRequest(BaseModel):
    user_id: int
    force: bool = False


class UserLevelModel(BaseModel):
    id: str
    name: str
    priority: int
    color: str
    hasAccess: bool
    customThemes: bool = False
    showRecommendations: bool = True
    canDownload: bool = True
    canRead: bool = True
    canUploadEpub: bool = False
    # Extra UI fields for new interface
    theme: Optional[str] = "dark"
    primaryColor: Optional[str] = "#3b82f6"
    fontSize: Optional[int] = 14
    glassBlur: Optional[int] = 12
    navOpacity: Optional[float] = 0.8
    accentOpacity: Optional[float] = 0.2
    glassOpacity: Optional[float] = 0.6
    backgroundColor: Optional[str] = "#0f172a"
    cardColor: Optional[str] = "#1e293b"
    forceSettings: bool = False


class AccessResponse(BaseModel):
    level: UserLevelModel
    hasAccess: bool
    isAdmin: bool
    isRealAdmin: bool = False
    isBetaTester: bool = False  # Controls new vs old UI
    customThemes: bool = False
    showRecommendations: bool = True
    allowThemeTemplates: bool = False
    nickname: Optional[str] = None
    name: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = []
    insignias: List[str] = []
    customStatus: Optional[str] = None
    role: Optional[str] = None
    status_label: Optional[str] = None  # Display label for user status
    hasLibraryAccess: bool = True
    canRequestBooks: bool = True
    canUploadEpub: bool = False
    ui_exported_settings: List[str] = []
    titlePreference: str = "romaji"


class LevelUpdate(BaseModel):
    id: str
    hasAccess: bool


class UpdateLevelsRequest(BaseModel):
    levels: List[LevelUpdate]


class UploadHistoryResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    book_hash: Optional[str] = None
    status: str
    final_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str  # Send as ISO string


# --- Routes ---


@router.post("/api/bot")
async def handle_bot_request(
    request: Request,
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """
    Main endpoint for Mini App requests.
    Dispatches actions: search, download, status, etc.
    """
    user_id = user_data.get("user_id", 0)
    user_level = user_data.get("level", "free")
    # Store for further use
    user_effective = user_data

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        body = {}

    action = body.get("action")
    data = body.get("data", {})

    # --- Control de Acceso por Niveles ---
    # Los administradores siempre tienen acceso.
    # El resto depende de su nivel (has_mini_app_access).
    if user_effective.get("has_mini_app_access") is False and action != "status":
        raise HTTPException(
            status_code=403, detail="Tu nivel de usuario no tiene acceso a la Mini App"
        )

    if action not in ["admin_get_system_logs", "admin_send_logs_telegram"]:
        logger.info(f"Miniapp action: {action} User: {user_id} Level: {user_level}")

    try:
        # Mapping of actions to their respective handlers
        from api.miniapp_handlers import (
            handle_search,
            handle_book_detail,
            handle_user_status,
            handle_user_downloads_history,
            handle_recommendations,
            handle_rate_book,
            handle_remove_rating,
            handle_rating_breakdown,
            handle_get_download_count,
            handle_save_badge_config,
            handle_status,
            handle_download,
            handle_bot_info,
            handle_ui_settings,
            handle_create_stars_invoice,
            handle_admin_stats,
            handle_admin_get_tiers,
            handle_admin_save_tier,
            handle_admin_get_users,
            handle_admin_set_user_level,
            handle_admin_backup_library,
            handle_admin_sync_users_cloud,
            handle_admin_scan_library,
            handle_admin_reset_library,
            handle_admin_restart_docker,
            handle_admin_update_system,
            handle_admin_save_tier_config,
            handle_admin_get_tier_config,
            handle_admin_save_user_permissions,
            handle_admin_get_user_permissions,
            handle_admin_find_duplicates,
            handle_admin_delete_duplicate,
            handle_admin_enrich_metadata,
            handle_update_user_setting,
            handle_get_user_audit_history,
            handle_admin_get_recent_audit_logs,
            handle_admin_get_themes,
            handle_admin_save_theme,
            handle_admin_sync_themes,
            handle_admin_get_theme_sync_logs,
            handle_admin_get_sync_status,
            handle_admin_force_sync,
            handle_admin_rename_themes,
            handle_admin_get_duplicates,
            handle_admin_clear_duplicates,
            handle_admin_scan_user,
            handle_admin_scan_series,
            handle_admin_get_system_logs,
            handle_admin_send_logs_telegram,
        )

        ACTION_HANDLERS = {
            "search": handle_search,
            "book-detail": handle_book_detail,
            "user_status": handle_user_status,
            "user_downloads_history": handle_user_downloads_history,
            "recommendations": handle_recommendations,
            "rate_book": handle_rate_book,
            "remove_rating": handle_remove_rating,
            "rating_breakdown": handle_rating_breakdown,
            "get_download_count": handle_get_download_count,
            "save_badge_config": handle_save_badge_config,
            "status": handle_status,
            "download": handle_download,
            "bot_info": handle_bot_info,
            "ui_settings": handle_ui_settings,
            "create_stars_invoice": handle_create_stars_invoice,
            "admin_stats": handle_admin_stats,
            "admin_get_tiers": handle_admin_get_tiers,
            "admin_save_tier": handle_admin_save_tier,
            "admin_get_users": handle_admin_get_users,
            "admin_set_user_level": handle_admin_set_user_level,
            "admin_backup_library": handle_admin_backup_library,
            "admin_sync_users_cloud": handle_admin_sync_users_cloud,
            "admin_scan_library": handle_admin_scan_library,
            "admin_reset_library": handle_admin_reset_library,
            "admin_restart_docker": handle_admin_restart_docker,
            "admin_update_system": handle_admin_update_system,
            "admin_save_tier_config": handle_admin_save_tier_config,
            "admin_get_tier_config": handle_admin_get_tier_config,
            "admin_save_user_permissions": handle_admin_save_user_permissions,
            "admin_get_user_permissions": handle_admin_get_user_permissions,
            "admin_get_recent_audit_logs": handle_admin_get_recent_audit_logs,
            "admin_get_themes": handle_admin_get_themes,
            "admin_save_theme": handle_admin_save_theme,
            "admin_sync_themes": handle_admin_sync_themes,
            "admin_get_theme_sync_logs": handle_admin_get_theme_sync_logs,
            "admin_get_sync_status": handle_admin_get_sync_status,
            "admin_force_sync": handle_admin_force_sync,
            "admin_rename_themes": handle_admin_rename_themes,
            "admin_find_duplicates": handle_admin_find_duplicates,
            "admin_delete_duplicate": handle_admin_delete_duplicate,
            "admin_enrich_metadata": handle_admin_enrich_metadata,
            "update_user_setting": handle_update_user_setting,
            "get_user_audit_history": handle_get_user_audit_history,
            "admin_get_duplicates": handle_admin_get_duplicates,
            "admin_clear_duplicates": handle_admin_clear_duplicates,
            "admin_scan_user": handle_admin_scan_user,
            "admin_scan_series": handle_admin_scan_series,
            "admin_get_system_logs": handle_admin_get_system_logs,
            "admin_send_logs_telegram": handle_admin_send_logs_telegram,
        }

        if action == "admin_bulk_upload_confirm":
            from api.miniapp_handlers import handle_admin_bulk_upload_confirm
            return await handle_admin_bulk_upload_confirm(data, user_effective)

        handler = ACTION_HANDLERS.get(action)
        if not handler:
            logger.warning(f"Unknown action requested: {action} by user {user_id}")
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

        if action not in ["admin_get_system_logs", "admin_send_logs_telegram"]:
            logger.info(f"Dispatching action '{action}' for user {user_id}")
        
        # Check if handler accepts request argument
        import inspect
        sig = inspect.signature(handler)
        if 'request' in sig.parameters:
            return await handler(data, user_effective, request=request)
        else:
            return await handler(data, user_effective)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling action {action}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# --- Nuevos Endpoints de Control de Acceso ---


@router.post("/api/user/access", response_model=AccessResponse)
async def check_user_access(
    request: AccessCheckRequest,
    user_data: Dict[str, Any] = Depends(get_current_user_data),
):
    from services.user_service import get_effective_user
    from repositories.user_repository import user_repo

    current_uid = user_data.get("user_id", 0)
    # Priorizar el ID verificado por Telegram
    uid = current_uid or request.user_id
    logger.info(f"Access check for UID: {uid} (Force: {request.force})")

    # 1. Unified Access Check
    # This single call now handles everything: Config, DB, Levels, and Personal Settings
    use_cache = not request.force
    eff = await get_effective_user(uid, use_cache=use_cache)

    # Everything we need is already in 'eff'
    is_admin = (eff.get("level") == "admin") or eff.get("is_admin_db", False)
    is_staff = eff.get("level") == "staff"
    has_access = eff.get("has_mini_app_access", False)

    # EMERGENCY OVERRIDE FOR SPECIFIC USER
    if uid == 133994080:
        logger.warning(f"🚨 Applying EMERGENCY clean settings for user {uid}")
        # Force clean structure
        eff["settings"] = {
            "theme": "dark",
            "primaryColor": "#3b82f6",
            "fontSize": 14,
            "navOpacity": 0.8,
            "accentOpacity": 0.2,
            "glassBlur": 12,
            "backgroundColor": "#0f172a",
            "cardColor": "#1e293b",
            "glassOpacity": 0.6,
            "cardGlowIntensity": 0.5,
            "showRecommendations": True
        }
        eff["nickname"] = "Admin"
        eff["username"] = "admin"

    access_info = eff.get("level_info", {})
    if not access_info:
        access_info = {
            "id": "6", "name": "Lector", "priority": 1, "color": "#9E9E9E", "hasAccess": True
        }

    # FORCED: New interface for everyone
    is_beta_tester = True 

    logger.info(
        f"Access response for UID {uid}: hasAccess={has_access}, isAdmin={is_admin}, isBetaTester={is_beta_tester} (FORCED VERSION)"
    )
    # Personal settings (showRecommendations) override level defaults
    user_settings = eff.get("settings", {})
    personal_show_recs = user_settings.get("showRecommendations")
    if personal_show_recs is None:
        personal_show_recs = user_settings.get("show_recommendations")
    
    # Final value: personal setting OR level default
    final_show_recommendations = (
        personal_show_recs if personal_show_recs is not None 
        else access_info.get("showRecommendations", True)
    )

    return AccessResponse(
        level=UserLevelModel(**access_info),
        hasAccess=has_access,
        isAdmin=is_admin,
        isRealAdmin=eff.get("is_real_admin", is_admin), # Use real admin status
        isBetaTester=is_beta_tester,
        customThemes=True, # Activar temas a todos
        showRecommendations=final_show_recommendations,
        allowThemeTemplates=access_info.get("allowThemeTemplates", False),
        nickname=access_info.get("nickname") or eff.get("nickname") or f"User_{uid}",
        name=access_info.get("name") or eff.get("name") or f"User_{uid}",
        username=access_info.get("username") or eff.get("username") or "",
        roles=access_info.get("roles") or eff.get("roles") or [],
        insignias=access_info.get("insignias") or eff.get("insignias") or [],
        customStatus=eff.get("role") or "",
        role=eff.get("role") or "user",
        status_label=eff.get("status_label") or "Lector",
        hasLibraryAccess=eff.get("has_library_access", True),
        canRequestBooks=eff.get("can_request_books", True),
        canUploadEpub=eff.get("can_upload_epub", access_info.get("canUploadEpub", False)),
        ui_exported_settings=eff.get("ui_exported_settings", ["theme", "primaryColor", "fontSize"]),
        titlePreference=user_settings.get("title_preference") or "romaji"
    )



@router.get("/api/admin/levels")
@router.get("/api/admin/access-levels")
async def get_levels(user_data: Dict[str, Any] = Depends(require_admin)):

    logger.info("Fetching all access levels")
    from repositories.user_repository import user_repo

    levels = await user_repo.get_all_levels()

    logger.info(f"Found {len(levels)} access levels")
    return {"levels": [UserLevelModel(**l) for l in levels]}


@router.put("/api/admin/levels")
@router.post("/api/admin/access-levels")
async def update_levels(
    request: UpdateLevelsRequest, user_data: Dict[str, Any] = Depends(require_admin)
):

    from repositories.user_repository import user_repo

    for level in request.levels:
        await user_repo.update_level_access(int(level.id), level.hasAccess)

    return {"success": True, "message": "Niveles actualizados correctamente"}
    
    
@router.post("/api/library/upload")
async def upload_epub_miniapp(
    file: UploadFile = File(...),
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """Sube un archivo EPUB y retorna su metadata para validación."""
    # Los admins y usuarios con permiso pueden subir
    if not user_data.get("can_upload_epub") and user_data.get("level") != "admin":
        raise HTTPException(
            status_code=403, detail="No tienes permiso para subir archivos EPUB"
        )
    
    if not file.filename.lower().endswith(".epub"):
        raise HTTPException(
            status_code=400, detail="Solo se admiten archivos EPUB (.epub)"
        )
    
    import tempfile
    from pathlib import Path
    from handlers.epub_upload_handler import epub_uploader, pending_uploads
    from datetime import datetime
    
    # Crear directorio temporal si no existe
    temp_dir = Path(tempfile.gettempdir()) / "zeepub_uploads"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Guardar archivo temporal
        temp_file = temp_dir / f"app_{user_data['user_id']}_{datetime.now().timestamp()}.epub"
        with open(temp_file, "wb") as f:
            f.write(await file.read())
        
        # Analizar EPUB
        metadata = await epub_uploader.analyze_epub(temp_file, file.filename, user_data['user_id'])
        
        if not metadata:
            if temp_file.exists():
                temp_file.unlink()
            
            # Log failure
            epub_uploader._log_history(
                user_id=user_data['user_id'],
                filename=file.filename,
                book_hash=None,
                status='error',
                error_message="Analysis failed (corrupt or invalid EPUB)"
            )
            
            raise HTTPException(
                status_code=400, detail="No se pudo procesar el archivo EPUB. Puede que esté corrupto o no sea válido."
            )
        
        # Guardar en pendientes
        upload_id = f"app_upload_{user_data['user_id']}_{datetime.now().timestamp()}"
        pending_uploads[upload_id] = {
            'file_path': str(temp_file),
            'metadata': metadata,
            'user_id': user_data['user_id'],
            'original_filename': file.filename
        }
        
        return {
            "success": True,
            "upload_id": upload_id,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in miniapp upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/library/upload/confirm")
async def confirm_epub_upload_miniapp(
    data: Dict[str, Any],
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """Confirma y finaliza la subida de un EPUB."""
    upload_id = data.get("upload_id")
    custom_path = data.get("path")
    
    from handlers.epub_upload_handler import epub_uploader, pending_uploads
    
    if upload_id not in pending_uploads:
        raise HTTPException(status_code=404, detail="Upload no encontrado o expirado")
    
    upload_info = pending_uploads[upload_id]
    
    # Verificar que el usuario sea el mismo o admin
    if upload_info['user_id'] != user_data['user_id'] and user_data.get("level") != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    try:
        from pathlib import Path
        file_path = Path(upload_info['file_path'])
        metadata = upload_info['metadata']
        
        # Usar ruta personalizada si se proporcionó
        suggested_path = custom_path or metadata.get('suggested_path')
        
        # Mover a la librería
        success = await epub_uploader.add_to_library(file_path, suggested_path, metadata)
        
        if success:
            # Log success
            epub_uploader._log_history(
                user_id=upload_info['user_id'],
                filename=upload_info['original_filename'],
                book_hash=metadata.get('book_hash'),
                status='success',
                final_path=suggested_path
            )
            
            # Limpiar
            epub_uploader.cleanup_upload(upload_id, file_path)
            return {"success": True, "path": suggested_path}
        else:
            # Log error
            epub_uploader._log_history(
                user_id=upload_info['user_id'],
                filename=upload_info['original_filename'],
                book_hash=metadata.get('book_hash'),
                status='error',
                error_message="Failed to move file to library"
            )
            raise HTTPException(status_code=500, detail="Error al mover el archivo a la librería")
            
    except Exception as e:
        logger.error(f"Error confirming upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/library/upload/bulk")
async def upload_epub_bulk(
    files: List[UploadFile] = File(...),
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """Sube múltiples EPUBs de una vez."""
    if not user_data.get("can_upload_epub") and user_data.get("level") != "admin":
        raise HTTPException(
            status_code=403, detail="No tienes permiso para subir archivos EPUB"
        )

    import tempfile
    from pathlib import Path
    from handlers.epub_upload_handler import epub_uploader, pending_uploads
    from datetime import datetime

    temp_dir = Path(tempfile.gettempdir()) / "zeepub_bulk_uploads"
    temp_dir.mkdir(exist_ok=True)

    results = []
    for file in files:
        if not file.filename.lower().endswith(".epub"):
            results.append({"filename": file.filename, "success": False, "error": "No es un EPUB"})
            continue

        try:
            temp_file = temp_dir / f"bulk_{user_data['user_id']}_{datetime.now().timestamp()}_{file.filename}"
            with open(temp_file, "wb") as f:
                f.write(await file.read())

            metadata = await epub_uploader.analyze_epub(temp_file, file.filename, user_data['user_id'])
            if not metadata:
                if temp_file.exists(): temp_file.unlink()
                results.append({"filename": file.filename, "success": False, "error": "Error de análisis"})
                continue

            upload_id = f"bulk_{user_data['user_id']}_{datetime.now().timestamp()}_{len(results)}"
            pending_uploads[upload_id] = {
                'file_path': str(temp_file),
                'metadata': metadata,
                'user_id': user_data['user_id'],
                'original_filename': file.filename,
                'is_bulk': True
            }

            results.append({
                "filename": file.filename,
                "success": True,
                "upload_id": upload_id,
                "metadata": metadata
            })
        except Exception as e:
            results.append({"filename": file.filename, "success": False, "error": str(e)})

    return {"results": results}


@router.post("/api/library/upload/bulk/confirm")
async def confirm_epub_upload_bulk_miniapp(
    data: Dict[str, Any],
    user_data: Dict[str, Any] = Depends(require_mini_app_access),
):
    """Confirma y finaliza múltiples subidas de EPUB."""
    from api.miniapp_handlers import handle_admin_bulk_upload_confirm
    return await handle_admin_bulk_upload_confirm(data, user_data)


@router.get("/api/admin/upload-history", response_model=List[UploadHistoryResponse])
async def get_upload_history(
    limit: int = 100,
    offset: int = 0,
    user_data: Dict[str, Any] = Depends(require_admin)
):
    """
    Obtiene el historial de subidas desde UploadHistory.
    """
    from api.miniapp_handlers import handle_get_upload_history
    return await handle_get_upload_history(limit, offset)
