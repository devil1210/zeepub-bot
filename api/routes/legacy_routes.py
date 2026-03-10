# api/routes/legacy_routes.py

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from api import miniapp_handlers
from api.deps import require_mini_app_access

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
            "bot_info": miniapp_handlers.handle_bot_info,
            "user_downloads_history": miniapp_handlers.handle_user_downloads_history,
            "recommendations": miniapp_handlers.handle_recommendations,
            "rate_book": miniapp_handlers.handle_rate_book,
            "remove_rating": miniapp_handlers.handle_remove_rating,
            "rating_breakdown": miniapp_handlers.handle_rating_breakdown,
            "request_book": miniapp_handlers.handle_request_book,
            "download": miniapp_handlers.handle_download,
            "ui_settings": miniapp_handlers.handle_ui_settings,
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

            logger.info(f"🤖 RPC Action: {action} (User: {user_data.get('user_id')})")

            # Execute handler
            result = await handler(data, user_data, request=request)
            return JSONResponse(content=result)

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
                "isBetaTester": user_data.get("beta_tester", False) or user_info.get("is_real_admin", False),
                "isAdmin": user_info.get("is_real_admin", False),
                "is_admin": user_info.get("is_real_admin", False),
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
