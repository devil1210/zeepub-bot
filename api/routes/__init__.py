# api/routes/__init__.py

from .admin_routes import AdminRoutes
from .agent_routes import AgentRoutes
from .auth_routes import AuthRoutes
from .config_routes import ConfigRoutes
from .editorial_routes import EditorialRoutes
from .legacy_routes import LegacyRoutes
from .library_routes import LibraryRoutes
from .media_routes import MediaRoutes
from .upload_routes import UploadRoutes

__all__ = [
    "AdminRoutes",
    "AgentRoutes",
    "AuthRoutes",
    "ConfigRoutes",
    "EditorialRoutes",
    "LegacyRoutes",
    "LibraryRoutes",
    "MediaRoutes",
    "UploadRoutes",
]
