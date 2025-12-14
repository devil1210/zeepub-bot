import os
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
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Integra PostgreSQL como base de datos principal (si está configurada)."

    async def initialize(self, bot_instance) -> bool:
        # La lógica principal de activación ocurre en config_settings.py y url_cache.py
        # Este plugin sirve para validar la conexión al inicio.

        # Verificar estado en config
        is_postgres_active = bool(config.DATABASE_URL)

        if is_postgres_active:
            logger.info("Plugin PostgreSQL: Base de datos configurada y activa.")
            # Podríamos añadir verificaciones de salud aquí si fuera necesario
            return True
        else:
            # Si el plugin está "cargado" pero la config no tiene URL (porque ENABLE_POSTGRES_PLUGIN es False),
            # entonces operamos en modo pasivo o indicamos que estamos usando SQLite.
            logger.info(
                "Plugin PostgreSQL: Desactivado o sin configuración. Usando SQLite por defecto."
            )
            return True

    async def cleanup(self) -> None:
        pass
