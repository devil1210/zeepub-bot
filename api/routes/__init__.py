# api/routes/__init__.py

from .admin_routes import AdminRoutes
from .agent_routes import AgentRoutes
from .auth_routes import AuthRoutes
from .config_routes import ConfigRoutes
from .legacy_routes import LegacyRoutes
from .library_routes import LibraryRoutes
from .media_routes import MediaRoutes

__all__ = [
    "LibraryRoutes",
    "AdminRoutes",
    "MediaRoutes",
    "AuthRoutes",
    "ConfigRoutes",
    "LegacyRoutes",
    "AgentRoutes",
]
