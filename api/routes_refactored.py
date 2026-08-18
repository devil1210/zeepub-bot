# api/routes_refactored.py

import logging

from .routes import AdminRoutes, AgentRoutes, AuthRoutes, ConfigRoutes, LegacyRoutes, LibraryRoutes, MediaRoutes
from .routes.upload_routes import UploadRoutes

logger = logging.getLogger(__name__)


class RoutesManager:
    """
    Refactored routes manager using SOLID principles.
    Single Responsibility: Routes coordination and orchestration.
    """

    def __init__(self):
        # Initialize all route handlers
        self.library_routes = LibraryRoutes()
        self.admin_routes = AdminRoutes()
        self.media_routes = MediaRoutes()
        self.auth_routes = AuthRoutes()
        self.config_routes = ConfigRoutes()
        self.legacy_routes = LegacyRoutes()
        self.upload_routes = UploadRoutes()  # 📤 REST upload endpoints para Web App
        self.agent_routes = AgentRoutes()  # 🌉 Puente MCP → SPbot

        # Register endpoint methods into routers
        self.library_routes.register_routes()
        self.admin_routes.register_routes()
        self.media_routes.register_routes()
        self.auth_routes.register_routes()
        self.config_routes.register_routes()
        self.legacy_routes.register_routes()
        self.upload_routes.register_routes()
        self.agent_routes.register_routes()

    def register_all_routes(self, app):
        """
        Register all route handlers with the FastAPI app.
        """
        try:
            logger.info("🔗 Registering all API routes")

            # Include all routers
            app.include_router(self.library_routes.get_router())
            app.include_router(self.admin_routes.get_router())
            app.include_router(self.media_routes.get_router())
            app.include_router(self.auth_routes.get_router())
            app.include_router(self.config_routes.get_router())
            app.include_router(self.legacy_routes.get_router())
            app.include_router(self.upload_routes.get_router())  # 📤 Upload REST
            app.include_router(self.upload_routes.get_admin_router())  # 📤 Admin upload history
            app.include_router(self.agent_routes.get_router())  # 🌉 Puente MCP

            logger.info("✅ All API routes registered successfully")

        except Exception as e:
            logger.error(f"❌ Error registering routes: {e}")
            raise

    def get_routes_stats(self) -> dict:
        """
        Get statistics about the refactored routes.
        """
        return {
            "total_routes": 5,
            "route_classes": ["LibraryRoutes", "AdminRoutes", "MediaRoutes", "AuthRoutes", "ConfigRoutes"],
            "avg_lines_per_route": 108,  # Down from 555/5 = 111 lines per route
            "responsibilities": {
                "LibraryRoutes": "Library content delivery and file management",
                "AdminRoutes": "Administrative operations and system management",
                "MediaRoutes": "Media content delivery and proxy services",
                "AuthRoutes": "Authentication, authorization, and token management",
                "ConfigRoutes": "Application configuration and user preferences",
            },
        }
