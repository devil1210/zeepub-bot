# api/routes/media_routes.py

import logging

from fastapi import APIRouter, Query
from fastapi.responses import RedirectResponse, Response

from api.main import bot

logger = logging.getLogger(__name__)


class MediaRoutes:
    """
    Handle media-related endpoints: avatars, images, files.
    Single Responsibility: Media content delivery and proxy services.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api")

    def get_router(self) -> APIRouter:
        """Return the configured router."""
        return self.router

    async def bot_avatar_proxy(self, file_id: str = Query(...)):
        """
        Proxies to bot's profile photo from Telegram.
        """
        try:
            logger.info(f"🖼️ Avatar proxy request: {file_id}")

            # Get file from Telegram bot
            file = await bot.app.bot.get_file(file_id)
            if not file.file_path:
                logger.error(f"No file_path found for file_id: {file_id}")
                return RedirectResponse(url="/robot-librarian.jpg")

            # Use httpx to download and stream to client
            import httpx

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(file.file_path)
                resp.raise_for_status()

                return Response(
                    content=resp.content,
                    media_type="image/jpeg",
                    headers={"Cache-Control": "public, max-age=31536000"},  # Cache for a year
                )

        except Exception as e:
            logger.error(f"❌ Error in avatar proxy: {e}")
            return RedirectResponse(url="/robot-librarian.jpg")

    def register_routes(self):
        """Register all media routes."""
        self.router.add_api_route(
            "/bot/avatar",
            self.bot_avatar_proxy,
            methods=["GET"],
            summary="Bot avatar proxy",
            description="Proxy to bot's profile photo from Telegram",
        )
