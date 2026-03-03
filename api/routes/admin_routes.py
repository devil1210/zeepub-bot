# api/routes/admin_routes.py

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from api.deps import require_mini_app_access

logger = logging.getLogger(__name__)


class AdminRoutes:
    """
    Handle admin-related endpoints: Facebook integration, bulk operations.
    Single Responsibility: Administrative operations and system management.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api")

    def get_router(self) -> APIRouter:
        """Return the configured router."""
        return self.router

    async def prepare_facebook_post(
        self,
        request: Request,
        user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
    ):
        """
        Prepara contenido para publicación en Facebook.
        """
        try:
            logger.info(f"📘 Facebook post preparation from user: {user_data.get('user_id', 'unknown')}")

            # Check admin permissions
            if not user_data.get("is_admin", False):
                return Response(content={"error": "Permiso denegado"}, status_code=403)

            # Parse request data
            data = await request.json()

            if not data or "book_id" not in data:
                return Response(content={"error": "book_id requerido"}, status_code=400)

            book_id = data["book_id"]

            # This would integrate with actual book service
            # For now, returning preparation data

            prep_data = {
                "status": "prepared",
                "book_id": book_id,
                "prepared_at": "2025-03-02T00:00:00Z",
                "facebook_data": {
                    "title": f"Libro {book_id}",
                    "description": "Descripción generada automáticamente",
                    "image_url": f"https://zeepub.com/covers/{book_id}.jpg",
                    "tags": ["novela ligera", "zeepub"],
                    "call_to_action": "Lee ahora en ZeePub",
                },
                "user": {"id": user_data.get("user_id"), "username": user_data.get("username", "")},
            }

            logger.info(f"✅ Facebook post prepared for book: {book_id}")
            return JSONResponse(content=prep_data)

        except Exception as e:
            logger.error(f"❌ Error preparing Facebook post: {e}")
            return Response(content={"error": "Error al preparar publicación"}, status_code=500)

    async def publish_facebook_post(
        self,
        request: Request,
        user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)],
    ):
        """
        Publica contenido preparado en Facebook.
        """
        try:
            logger.info(f"📘 Facebook post publication from user: {user_data.get('user_id', 'unknown')}")

            # Check admin permissions
            if not user_data.get("is_admin", False):
                return Response(content={"error": "Permiso denegado"}, status_code=403)

            # Parse request data
            data = await request.json()

            if not data or "post_id" not in data:
                return Response(content={"error": "post_id requerido"}, status_code=400)

            post_id = data["post_id"]

            # This would integrate with actual Facebook API
            # For now, simulating publication

            publish_data = {
                "status": "published",
                "post_id": post_id,
                "published_at": "2025-03-02T00:00:00Z",
                "facebook_url": f"https://facebook.com/posts/{post_id}",
                "user": {"id": user_data.get("user_id"), "username": user_data.get("username", "")},
            }

            logger.info(f"✅ Facebook post published: {post_id}")
            return JSONResponse(content=publish_data)

        except Exception as e:
            logger.error(f"❌ Error publishing Facebook post: {e}")
            return Response(content={"error": "Error al publicar en Facebook"}, status_code=500)

    def register_routes(self):
        """Register all admin routes."""
        self.router.add_api_route(
            "/facebook/prepare",
            self.prepare_facebook_post,
            methods=["POST"],
            summary="Prepare Facebook post",
            description="Prepare content for Facebook publication",
        )

        self.router.add_api_route(
            "/facebook/publish",
            self.publish_facebook_post,
            methods=["POST"],
            summary="Publish Facebook post",
            description="Publish prepared content to Facebook",
        )
