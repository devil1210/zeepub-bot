import logging
from plugins.base_plugin import BasePlugin
from config.config_settings import config

logger = logging.getLogger(__name__)


class PostgresPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "postgres_plugin"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "Gestión de la base de datos PostgreSQL (Mandatorio)."

    async def initialize(self, bot_instance) -> bool:
        # La lógica principal de activación ocurre en DatabaseManager
        # Este plugin sirve para validar la conexión al inicio.

        # Verificar estado en config
        is_postgres_active = bool(config.DATABASE_URL)

        if is_postgres_active:
            logger.info("Plugin PostgreSQL: Base de datos configurada y activa.")
            return True
        else:
            logger.error(
                "Plugin PostgreSQL: ERROR. DATABASE_URL no configurada. Postgres es obligatorio."
            )
            return False

    async def cleanup(self) -> None:
        pass
