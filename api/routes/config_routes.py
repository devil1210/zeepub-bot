# api/routes/config_routes.py

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from api.deps import require_mini_app_access

logger = logging.getLogger(__name__)


class ConfigRoutes:
    """
    Handle configuration-related endpoints: app config, strings, settings.
    Single Responsibility: Application configuration and user preferences.
    """

    def __init__(self):
        self.router = APIRouter(prefix="/api")

    def get_router(self) -> APIRouter:
        """Return the configured router."""
        return self.router

    async def get_config(self, user_data: Annotated[dict[str, Any], Depends(require_mini_app_access)]):
        """
        Retorna configuración inicial para la Mini App, incluyendo permisos de admin y publisher.
        """
        try:
            logger.info(f"⚙️ Config request from user: {user_data.get('user_id', 'unknown')}")

            # Extract user roles and permissions
            user_roles = user_data.get("roles", [])
            user_permissions = user_data.get("permissions", [])

            # Build configuration object
            app_config = {
                "app": {
                    "name": "ZeePub Mini App",
                    "version": "2.0.0",
                    "description": "Biblioteca personal de novelas ligeras y manga",
                },
                "user": {
                    "id": user_data.get("user_id"),
                    "username": user_data.get("username", ""),
                    "roles": user_roles,
                    "permissions": user_permissions,
                    "level": user_data.get("level", "free"),
                    "is_admin": user_data.get("is_admin", False),
                    "is_publisher": user_data.get("is_publisher", False),
                },
                "features": {
                    "library_access": "library" in user_permissions,
                    "download_books": "download:books" in user_permissions,
                    "upload_books": "upload:books" in user_permissions,
                    "bulk_operations": "bulk:operations" in user_permissions,
                    "admin_panel": "admin:panel" in user_permissions,
                },
                "ui": {"theme": "dark", "language": "es", "auto_download": True, "show_covers": True},
                "limits": {
                    "daily_downloads": user_data.get("daily_limit", 10),
                    "weekly_downloads": user_data.get("weekly_limit", 50),
                    "monthly_downloads": user_data.get("monthly_limit", 200),
                    "max_file_size": user_data.get("max_file_size", 50 * 1024 * 1024),  # 50MB
                },
            }

            logger.info(f"✅ Config generated successfully for user {user_data.get('user_id')}")
            return JSONResponse(content=app_config)

        except Exception as e:
            logger.error(f"❌ Error generating config: {e}")
            return Response(content={"error": "Error al obtener configuración"}, status_code=500)

    async def get_app_strings(self, request: Request):
        """
        Obtiene los textos personalizados para la Mini App.
        """
        try:
            logger.info("📝 App strings request")

            # Get user language preference (from headers or default)
            user_language = request.headers.get("Accept-Language", "es").split(",")[0].strip()

            # Define strings based on language
            strings = {
                "es": {
                    "app_name": "ZeePub",
                    "welcome": "Bienvenido a tu biblioteca",
                    "search_placeholder": "Buscar libros...",
                    "download": "Descargar",
                    "upload": "Subir libro",
                    "settings": "Configuración",
                    "library": "Biblioteca",
                    "profile": "Mi perfil",
                    "logout": "Cerrar sesión",
                    "error_generic": "Ha ocurrido un error",
                    "loading": "Cargando...",
                    "no_results": "No se encontraron resultados",
                    "confirm": "Confirmar",
                    "cancel": "Cancelar",
                },
                "en": {
                    "app_name": "ZeePub",
                    "welcome": "Welcome to your library",
                    "search_placeholder": "Search books...",
                    "download": "Download",
                    "upload": "Upload book",
                    "settings": "Settings",
                    "library": "Library",
                    "profile": "My profile",
                    "logout": "Logout",
                    "error_generic": "An error has occurred",
                    "loading": "Loading...",
                    "no_results": "No results found",
                    "confirm": "Confirm",
                    "cancel": "Cancel",
                },
            }

            # Get strings for user language or fallback to Spanish
            user_strings = strings.get(user_language, strings.get("es", {}))

            # Add metadata about strings
            response_data = {
                "language": user_language,
                "strings": user_strings,
                "last_updated": "2025-03-02T00:00:00Z",
                "version": "2.0.0",
            }

            logger.info(f"✅ App strings generated for language: {user_language}")
            return JSONResponse(content=response_data)

        except Exception as e:
            logger.error(f"❌ Error generating app strings: {e}")
            return Response(content={"error": "Error al obtener textos"}, status_code=500)

    def register_routes(self):
        """Register all configuration routes."""
        self.router.add_api_route(
            "/config",
            self.get_config,
            methods=["GET"],
            summary="Get app configuration",
            description="Get Mini App configuration including user permissions and settings",
        )

        self.router.add_api_route(
            "/app-strings",
            self.get_app_strings,
            methods=["GET"],
            summary="Get app strings",
            description="Get localized strings for the Mini App interface",
        )
