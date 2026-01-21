import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
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


class AccessResponse(BaseModel):
    level: UserLevelModel
    hasAccess: bool
    isAdmin: bool
    isBetaTester: bool = False  # Controls new vs old UI
    customThemes: bool = False
    showRecommendations: bool = True
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
    ui_exported_settings: List[str] = []


class LevelUpdate(BaseModel):
    id: str
    hasAccess: bool


class UpdateLevelsRequest(BaseModel):
    levels: List[LevelUpdate]


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
    except Exception:
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
            handle_admin_get_duplicates,
            handle_admin_clear_duplicates,
            handle_admin_scan_user,
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
            "admin_find_duplicates": handle_admin_find_duplicates,
            "admin_delete_duplicate": handle_admin_delete_duplicate,
            "admin_enrich_metadata": handle_admin_enrich_metadata,
            "update_user_setting": handle_update_user_setting,
            "get_user_audit_history": handle_get_user_audit_history,
            "admin_get_duplicates": handle_admin_get_duplicates,
            "admin_clear_duplicates": handle_admin_clear_duplicates,
            "admin_scan_user": handle_admin_scan_user,
        }

        handler = ACTION_HANDLERS.get(action)
        if not handler:
            logger.warning(f"Unknown action requested: {action} by user {user_id}")
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

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
    is_beta_tester = is_admin or eff.get("isBetaTester", False)

    logger.debug(
        f"Access response for UID {uid}: hasAccess={has_access}, isAdmin={is_admin}"
    )

    access_info = eff.get("level_info", {})
    if not access_info:
        # Fallback if somehow not populated
        access_info = {
            "id": "6", "name": "Lector", "priority": 1, "color": "#9E9E9E", "hasAccess": False
        }

    # Beta tester flag - admins are always beta testers
    is_beta_tester = is_admin or access_info.get("isBetaTester", False)

    logger.info(
        f"Access response for UID {uid}: hasAccess={has_access}, isAdmin={is_admin}, isBetaTester={is_beta_tester}"
    )
    # Personal settings (showRecommendations) override level defaults
    user_settings = eff.get("settings", {})
    personal_show_recs = user_settings.get("showRecommendations")
    if personal_show_recs is None:
        personal_show_recs = user_settings.get("show_recommendations")
    
    # Final value: personal setting OR level default
    final_show_recommendations = (
        personal_show_recs if personal_show_recs is not None 
        else access_info["level"].get("showRecommendations", True)
    )

    return AccessResponse(
        level=UserLevelModel(**access_info["level"]),
        hasAccess=has_access,
        isAdmin=is_admin,
        isBetaTester=is_beta_tester,
        customThemes=access_info["level"].get("customThemes", False) or is_admin,
        showRecommendations=final_show_recommendations,
        nickname=access_info.get("nickname") or eff.get("nickname"),
        name=access_info.get("name") or eff.get("name"),
        username=access_info.get("username") or eff.get("username"),
        roles=access_info.get("roles") or eff.get("roles") or [],
        insignias=access_info.get("insignias") or eff.get("insignias") or [],
        customStatus=eff.get("role"),
        role=eff.get("role"),
        status_label=eff.get("status_label"),
        hasLibraryAccess=eff.get("has_library_access", True),
        canRequestBooks=eff.get("can_request_books", True),
        ui_exported_settings=eff.get("ui_exported_settings", ["theme", "primaryColor", "fontSize"])
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
