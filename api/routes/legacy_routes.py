import os
import logging
from typing import Annotated, Any
import aiofiles

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse

from api import miniapp_handlers
from api.deps import require_mini_app_access
from services.library_service import LibraryService

logger = logging.getLogger(__name__)


class LegacyRoutes:
    """
    Handle legacy endpoints and RPC-style bot actions.
    Maintains compatibility with the v3.x frontend.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api")
        # Action map for /api/bot RPC dispatcher
        self.action_map = {
            "search": miniapp_handlers.handle_search,
            "search_volumes": miniapp_handlers.handle_search_volumes,
            "book-detail": miniapp_handlers.handle_book_detail,
            "user_status": miniapp_handlers.handle_user_status,
            "status": miniapp_handlers.handle_status,
            "feedback": miniapp_handlers.handle_feedback,
            "link_telegram": miniapp_handlers.handle_link_telegram,
            "link-telegram": miniapp_handlers.handle_link_telegram,
            "unlink_telegram": miniapp_handlers.handle_unlink_telegram,
            "unlink-telegram": miniapp_handlers.handle_unlink_telegram,
            "telegram_widget_auth": miniapp_handlers.handle_telegram_widget_auth,
            "telegram-widget-auth": miniapp_handlers.handle_telegram_widget_auth,
            "generate_qr_auth": miniapp_handlers.handle_generate_qr_auth,
            "generate-qr-auth": miniapp_handlers.handle_generate_qr_auth,
            "check_qr_auth": miniapp_handlers.handle_check_qr_auth,
            "check-qr-auth": miniapp_handlers.handle_check_qr_auth,
            "bot_info": miniapp_handlers.handle_bot_info,
            "user_downloads_history": miniapp_handlers.handle_user_downloads_history,
            "recommendations": miniapp_handlers.handle_recommendations,
            "rate_book": miniapp_handlers.handle_rate_book,
            "remove_rating": miniapp_handlers.handle_remove_rating,
            "rating_breakdown": miniapp_handlers.handle_rating_breakdown,
            "request_book": miniapp_handlers.handle_request_book,
            "download": miniapp_handlers.handle_download,
            "ui_settings": miniapp_handlers.handle_ui_settings,
            # Admin Actions
            "admin_get_system_logs": miniapp_handlers.handle_admin_get_system_logs,
            "admin_send_logs_telegram": miniapp_handlers.handle_admin_send_logs_telegram,
            "admin_stats": miniapp_handlers.handle_admin_stats,
            "admin_get_users": miniapp_handlers.handle_admin_get_users,
            "admin_get_tiers": miniapp_handlers.handle_admin_get_tiers,
            "admin_get_tier_config": miniapp_handlers.handle_admin_get_tier_config,
            "admin_get_themes": miniapp_handlers.handle_admin_get_themes,
            "admin_get_recent_audit_logs": miniapp_handlers.handle_admin_get_recent_audit_logs,
            "admin_get_sync_status": miniapp_handlers.handle_admin_get_sync_status,
            "admin_scan_library": miniapp_handlers.handle_admin_scan_library,
            "admin_scan_status": miniapp_handlers.handle_admin_scan_status,
            "admin_save_tier": miniapp_handlers.handle_admin_save_tier,
            "admin_set_user_level": miniapp_handlers.handle_admin_set_user_level,
            "admin_delete_user": miniapp_handlers.handle_admin_delete_user,
            "admin_backup_library": miniapp_handlers.handle_admin_backup_library,
            "admin_sync_users_cloud": miniapp_handlers.handle_admin_sync_users_cloud,
            "admin_sync_library_cloud": miniapp_handlers.handle_admin_sync_library_cloud,
            "admin_cleanup_library": miniapp_handlers.handle_admin_cleanup_library,
            "admin_scan_series": miniapp_handlers.handle_admin_scan_series,
            "admin_enrich_metadata": miniapp_handlers.handle_admin_enrich_metadata,
            "admin_reset_library": miniapp_handlers.handle_admin_reset_library,
            "admin_restart_docker": miniapp_handlers.handle_admin_restart_docker,
            "admin_update_system": miniapp_handlers.handle_admin_update_system,
            "admin_update_covers": miniapp_handlers.handle_admin_update_covers,
            "admin_stop_scan": miniapp_handlers.handle_admin_stop_scan,
            "admin_save_tier_config": miniapp_handlers.handle_admin_save_tier_config,
            "admin_get_user_permissions": miniapp_handlers.handle_admin_get_user_permissions,
            "admin_save_user_permissions": miniapp_handlers.handle_admin_save_user_permissions,
            "get_user_audit_history": miniapp_handlers.handle_get_user_audit_history,
            "admin_save_theme": miniapp_handlers.handle_admin_save_theme,
            "admin_sync_themes": miniapp_handlers.handle_admin_sync_themes,
            "admin_rename_themes": miniapp_handlers.handle_admin_rename_themes,
            "admin_get_theme_sync_logs": miniapp_handlers.handle_admin_get_theme_sync_logs,
            "admin_scan_user": miniapp_handlers.handle_admin_scan_user,
            "admin_get_genre_audits": miniapp_handlers.handle_admin_get_genre_audits,
            "admin_resolve_genre_audit": miniapp_handlers.handle_admin_resolve_genre_audit,
            "admin_get_library_grid": miniapp_handlers.handle_admin_get_library_grid,
            "admin_update_series_grid": miniapp_handlers.handle_admin_update_series_grid,
            "admin_update_book_grid": miniapp_handlers.handle_admin_update_book_grid,
            "admin_bulk_save_grid": miniapp_handlers.handle_admin_bulk_save_grid,
            "admin_recalculate_series_slug": miniapp_handlers.handle_admin_recalculate_series_slug,
            "bulk_analyze_library": miniapp_handlers.handle_bulk_analyze_library,
            "bulk_update_metadata": miniapp_handlers.handle_bulk_update_metadata,
            "bulk_get_job_status": miniapp_handlers.handle_bulk_get_job_status,
            "admin_bulk_upload_confirm": miniapp_handlers.handle_admin_bulk_upload_confirm,
            "get_upload_history": miniapp_handlers.handle_get_upload_history,
            # Bulk hypenated actions compatibility for React frontend
            "bulk-analyze-library": miniapp_handlers.handle_bulk_analyze_library,
            "bulk-update-metadata": miniapp_handlers.handle_bulk_update_metadata,
            "bulk-get-job-status": miniapp_handlers.handle_bulk_get_job_status,
            # AI Hub Actions
            "ai_stats": miniapp_handlers.handle_ai_stats,
            "ai_get_proposals": miniapp_handlers.handle_ai_get_proposals,
            "ai_get_lists": miniapp_handlers.handle_ai_get_lists,
            "ai_scan_series": miniapp_handlers.handle_ai_scan_series,
            "ai_apply_changes": miniapp_handlers.handle_ai_apply_changes,
            "ai_toggle_background_scan": miniapp_handlers.handle_ai_toggle_background_scan,
            "ai_reject_proposal": miniapp_handlers.handle_ai_reject_proposal,
            "ai_apply_merge": miniapp_handlers.handle_ai_apply_merge,
            "ai_reset_series": miniapp_handlers.handle_ai_reset_series,
            "ai_recalculate_all_slugs": miniapp_handlers.handle_ai_recalculate_all_slugs,
            "admin_get_ai_scan_status": miniapp_handlers.handle_admin_get_ai_scan_status,
            # Observatory Actions
            "observatory_overview": miniapp_handlers.handle_observatory_overview,
            "observatory_executions": miniapp_handlers.handle_observatory_executions,
            "observatory_publications": miniapp_handlers.handle_observatory_publications,
            "observatory_metrics": miniapp_handlers.handle_observatory_metrics,
            # Duplicates / Resolution Center Actions
            "admin_get_duplicates": miniapp_handlers.handle_admin_get_duplicates,
            "admin_recheck_duplicates": miniapp_handlers.handle_admin_recheck_duplicates,
            "admin_clear_duplicates": miniapp_handlers.handle_admin_clear_duplicates,
            "admin_delete_duplicate_item": miniapp_handlers.handle_admin_delete_duplicate_item,
            "admin_ai_series_duplicate_scan": miniapp_handlers.handle_admin_ai_series_duplicate_scan,
            "admin_merge_series": miniapp_handlers.handle_admin_merge_series,
            # Publisher / Publication Actions
            "pub_get_queue": miniapp_handlers.handle_pub_get_queue,
            "pub_get_channels": miniapp_handlers.handle_pub_get_channels,
            "pub_get_templates": miniapp_handlers.handle_pub_get_templates,
            "pub_save_channel": miniapp_handlers.handle_pub_save_channel,
            "pub_delete_channel": miniapp_handlers.handle_pub_delete_channel,
            "pub_toggle_favorite": miniapp_handlers.handle_pub_toggle_favorite,
            "pub_promote_discovered": miniapp_handlers.handle_pub_promote_discovered,
            "pub_save_template": miniapp_handlers.handle_pub_save_template,
            "pub_delete_template": miniapp_handlers.handle_pub_delete_template,
            "pub_schedule": miniapp_handlers.handle_pub_schedule,
            "pub_update_queue_item": miniapp_handlers.handle_pub_update_queue_item,
            "pub_delete_queue_item": miniapp_handlers.handle_pub_delete_queue_item,
            "pub_restore_templates": miniapp_handlers.handle_pub_restore_templates,
            "pub_quick_post": miniapp_handlers.handle_pub_quick_post,
            "pub_update_post": miniapp_handlers.handle_pub_update_post,
            "pub-update-post": miniapp_handlers.handle_pub_update_post,
            "pub_check_facebook_album": miniapp_handlers.handle_pub_check_facebook_album,
        }

    def get_router(self) -> APIRouter:
        return self.router

    async def bot_rpc_dispatcher(
        self,
        request: Request,
        user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
    ):
        """
        Generic dispatcher for /api/bot RPC calls.
        """
        try:
            body = await request.json()
            action = body.get("action")
            data = body.get("data", {})

            if not action:
                return JSONResponse(content={"error": "Action required"}, status_code=400)

            handler = self.action_map.get(action)
            if not handler:
                logger.warning(f"⚠️ Unknown RPC action requested: {action}")
                return JSONResponse(content={"error": f"Unknown action: {action}"}, status_code=400)

            logger.info(f"🤖 RPC Action: {action} (User: {user_data.get('user_id') or user_data.get('id')})")
            from inspect import signature

            # Execute handler only with supported arguments
            sig = signature(handler)
            if "request" in sig.parameters:
                result = await handler(data, user_data, request=request)
            else:
                result = await handler(data, user_data)

            if result is not None:
                return JSONResponse(content=jsonable_encoder(result))
            return JSONResponse(content={"error": "No result from handler"}, status_code=500)

        except HTTPException as he:
            # Propagate HTTP errors with their real status code (404, 400, etc.)
            return JSONResponse(
                content={"success": False, "error": he.detail},
                status_code=he.status_code,
            )
        except Exception as e:
            logger.error(
                f"❌ Error in RPC dispatcher ({action if 'action' in locals() else 'unknown'}): {e}", exc_info=True
            )
            return JSONResponse(content={"error": str(e)}, status_code=500)

    async def get_user_access_legacy(
        self,
        request: Request,
        user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
    ):
        """
        Legacy POST /api/user/access endpoint.
        """
        try:
            # Re-use the handler logic from api.handlers.users.handle_user_status
            # but adapted to the access format expected by the frontend
            from api.handlers.users import handle_user_status

            status_data = await handle_user_status({}, user_data)
            user_info = status_data.get("user", {})

            # Additional flags for legacy compatibility
            legacy_access = {
                "user_id": user_info.get("id"),
                "username": user_info.get("username"),
                "isBetaTester": user_data.get("beta_tester", False)
                or user_info.get("is_real_admin", False)
                or user_info.get("level") == "admin",
                "isAdmin": user_info.get("is_real_admin", False) or user_info.get("level") == "admin",
                "is_admin": user_info.get("is_real_admin", False) or user_info.get("level") == "admin",
                "is_real_admin": user_info.get("is_real_admin", False) or user_info.get("level") == "admin",
                "isStaff": user_info.get("level") in ("admin", "staff"),
                "role": user_info.get("role"),
                "status_label": user_info.get("status_label"),
                "custom_themes": True,  # For admins/staff
                "allow_theme_templates": user_info.get("is_real_admin", False),
                "hasLibraryAccess": user_info.get("has_library_access", True),
                "canRequestBooks": user_info.get("can_request_books", True),
                "canUploadEpub": user_info.get("can_upload_epub", False),
                "nickname": user_data.get("nickname"),
                "name": user_data.get("name"),
                "roles": user_data.get("roles", []),
                "insignias": user_data.get("insignias", []),
                "ui_exported_settings": ["theme", "primaryColor", "glassBlur", "glassOpacity"],
            }

            return JSONResponse(content=legacy_access)
        except Exception as e:
            logger.error(f"❌ Error in legacy access endpoint: {e}")
            return JSONResponse(content={"error": str(e)}, status_code=500)

    async def handle_direct_download(
        self,
        book_id: str,
        request: Request,
    ):
        """Descarga directa de un EPUB en el navegador."""
        book_hash = book_id.replace("local_", "").replace("series_", "")
        book = await LibraryService.get_book_by_hash(book_hash)
        if not book:
            volumes = await LibraryService.get_series_volumes(book_hash, limit=1)
            if volumes:
                book = volumes[0]
        file_path = book.get("filepath") or book.get("file_path") if book else None
        if not book or not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Archivo EPUB no encontrado en el servidor")
        title = book.get("title") or book.get("clean_title") or "libro"
        safe_title = "".join([c for c in title if c.isalnum() or c in (" ", "_", "-")]).rstrip()

        async def iterfile_async():
            async with aiofiles.open(file_path, mode="rb") as f:
                while chunk := await f.read(64 * 1024):
                    yield chunk

        return StreamingResponse(
            content=iterfile_async(),
            media_type="application/epub+zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_title}.epub"',
                "Cache-Control": "public, max-age=3600",
            },
        )

    def register_routes(self):
        """Register endpoints."""
        self.router.add_api_route(
            "/bot",
            self.bot_rpc_dispatcher,
            methods=["POST"],
            summary="Bot RPC Dispatcher",
        )
        self.router.add_api_route(
            "/user/access",
            self.get_user_access_legacy,
            methods=["POST"],
            summary="Legacy User Access",
        )
        self.router.add_api_route(
            "/bot/download_file/{book_id}",
            self.handle_direct_download,
            methods=["GET"],
            summary="Direct EPUB File Download",
        )
