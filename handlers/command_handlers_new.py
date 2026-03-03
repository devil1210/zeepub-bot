# handlers/command_handlers_new.py

import logging

from .commands import (
    AdminHandler,
    AuthHandler,
    CancelHandler,
    CatalogHandler,
    EvilHandler,
    PluginsHandler,
    SearchHandler,
    StartHandler,
    StatusHandler,
)

logger = logging.getLogger(__name__)


class CommandHandlersNew:
    """
    Refactored command handlers using Single Responsibility Principle.
    Each handler has a specific, focused responsibility.
    """

    def __init__(self, app):
        self.app = app
        from services.settings_service import SettingsService

        self.settings_service = SettingsService()

        # Initialize specialized handlers
        self.start_handler = StartHandler(app)
        self.catalog_handler = CatalogHandler(app)
        self.status_handler = StatusHandler(app)
        self.cancel_handler = CancelHandler(app)
        self.search_handler = SearchHandler(app)
        self.admin_handler = AdminHandler(app)
        self.auth_handler = AuthHandler(app)
        self.plugins_handler = PluginsHandler(app)
        self.evil_handler = EvilHandler(app)

        # Register all handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register all command handlers with the Telegram app."""
        from telegram.ext import CommandHandler

        # Core user commands
        self.app.add_handler(CommandHandler("search", self.search_handler.handle))
        self.app.add_handler(CommandHandler("start", self.start_handler.handle))
        self.app.add_handler(CommandHandler("status", self.status_handler.handle))
        self.app.add_handler(CommandHandler("cancel", self.cancel_handler.handle))
        self.app.add_handler(CommandHandler("plugins", self.plugins_handler.handle))
        self.app.add_handler(CommandHandler("evil", self.evil_handler.handle))
        self.app.add_handler(CommandHandler("changeweb", self.auth_handler.handle))
        self.app.add_handler(CommandHandler("acceso_web", self.auth_handler.handle))

        # Catalog commands (both Spanish and English)
        self.app.add_handler(CommandHandler("catalog", self.catalog_handler.handle))
        self.app.add_handler(CommandHandler("catalogo", self.catalog_handler.handle))

    def get_handler_stats(self) -> dict:
        """Get statistics about the refactored handlers."""
        return {
            "total_handlers": 9,
            "handler_classes": [
                "StartHandler",
                "CatalogHandler",
                "StatusHandler",
                "CancelHandler",
                "SearchHandler",
                "AdminHandler",
                "AuthHandler",
                "PluginsHandler",
                "EvilHandler",
            ],
            "avg_lines_per_handler": 72,  # Down from 654/9 = 72.7 lines per handler
            "responsibilities": {
                "StartHandler": "User onboarding and state management",
                "CatalogHandler": "Library browsing and navigation",
                "StatusHandler": "User information and account status",
                "CancelHandler": "State management and operation cancellation",
                "SearchHandler": "Search functionality and results display",
                "AdminHandler": "Administrative operations and system management",
                "AuthHandler": "Web interface authentication and access management",
                "PluginsHandler": "Plugin management and system information",
                "EvilHandler": "System maintenance and security operations",
            },
        }
