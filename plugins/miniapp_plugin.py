import logging
import os

from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class MiniAppPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "miniapp_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Maneja la integración con la Mini App de Telegram (Web App)."

    async def initialize(self, bot_instance) -> bool:
        self.enabled = os.getenv("ENABLE_MINI_APP", "True").lower() == "true"

        if not self.enabled:
            logger.info("Plugin Mini App desactivado por configuración.")
            return False

        try:
            from handlers.webapp_handlers import register_handlers

            register_handlers(bot_instance)
            logger.info("Plugin Mini App: Handlers registrados.")
            return True
        except Exception as e:
            logger.error(f"Error registrando handlers del plugin Mini App: {e}")
            return False

    async def cleanup(self) -> None:
        pass
