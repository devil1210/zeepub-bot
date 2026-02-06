# config/config_settings.py

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime

from dotenv import load_dotenv

load_dotenv(override=False)


@dataclass
class BotConfig:
    TELEGRAM_TOKEN: str = field(default_factory=lambda: os.getenv("TELEGRAM_TOKEN", ""))
    VERSION: str = "v8.5.0-PG-STABLE"

    # Dominio público (ej: zp-dev.sp-core.xyz o zeepub-bot.sp-core.xyz)
    PUBLIC_DOMAIN: str = os.getenv("PUBLIC_DOMAIN", "")

    # Si no se define BASE_URL, se construye usando PUBLIC_DOMAIN
    BASE_URL: str = os.getenv("BASE_URL", "")

    # URL de la Mini App (para botones y referencias)
    WEBAPP_URL: str = os.getenv("WEBAPP_URL", "")

    SECRET_SEED: str = os.getenv("SECRET_SEED", "")

    # Administradores (no tienen descargas ilimitadas aquí)
    ADMIN_USERS: set[int] = field(
        default_factory=lambda: {
            int(x.strip()) for x in os.getenv("ADMIN_USERS", "").split(",") if x.strip().isdigit()
        }
    )

    # Listas de usuarios con distintos niveles
    WHITELIST: set[int] = field(
        default_factory=lambda: {
            int(x.strip()) for x in os.getenv("WHITELIST", "").split(",") if x.strip().isdigit()
        }
    )
    VIP_LIST: set[int] = field(
        default_factory=lambda: {
            int(x.strip()) for x in os.getenv("VIP_LIST", "").split(",") if x.strip().isdigit()
        }
    )
    PREMIUM_LIST: set[int] = field(
        default_factory=lambda: {
            int(x.strip()) for x in os.getenv("PREMIUM_LIST", "").split(",") if x.strip().isdigit()
        }
    )

    # Facebook Publishers
    FACEBOOK_PUBLISHERS: set[int] = field(
        default_factory=lambda: {
            int(x.strip())
            for x in os.getenv("FACEBOOK_PUBLISHERS", "").split(",")
            if x.strip().isdigit()
        }
    )

    # Facebook Credentials
    FACEBOOK_PAGE_ACCESS_TOKEN: str = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
    FACEBOOK_GROUP_ID: str = os.getenv("FACEBOOK_GROUP_ID", "")

    # Domain for public downloads
    DL_DOMAIN: str = os.getenv("DL_DOMAIN", "dl.zeepubs.com")

    # ZITADEL Actions v2 - Signing Key para validación de webhooks
    ZITADEL_SIGNING_KEY: str = os.getenv("ZITADEL_SIGNING_KEY", "")

    # Donation URL
    DONATION_URL: str = os.getenv("DONATION_URL", "")

    # Límites por hora
    MAX_DOWNLOADS_PER_DAY: int = int(os.getenv("MAX_DOWNLOADS_PER_DAY", "5"))
    WHITELIST_DOWNLOADS_PER_DAY: int = int(os.getenv("WHITELIST_DOWNLOADS_PER_DAY", "10"))
    VIP_DOWNLOADS_PER_DAY: int = int(os.getenv("VIP_DOWNLOADS_PER_DAY", "20"))

    # Otros ajustes
    MAX_IN_MEMORY_BYTES: int = int(os.getenv("MAX_IN_MEMORY_BYTES", "10485760"))
    DEFAULT_AIOHTTP_TIMEOUT: int = int(os.getenv("AIOHTTP_TIMEOUT", "60"))
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "20"))
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    ENABLE_PLUGINS: bool = os.getenv("ENABLE_PLUGINS", "true").lower() == "true"
    PLUGIN_DIRECTORY: str = os.getenv("PLUGIN_DIRECTORY", "plugins")

    # Plugin PostgreSQL
    ENABLE_POSTGRES_PLUGIN: bool = os.getenv("ENABLE_POSTGRES_PLUGIN", "True").lower() == "true"

    # Plugin Group Manager
    ENABLE_GROUP_MANAGER: bool = os.getenv("ENABLE_GROUP_MANAGER", "True").lower() == "true"

    # Plugin System Manager
    ENABLE_SYSTEM_MANAGER: bool = os.getenv("ENABLE_SYSTEM_MANAGER", "True").lower() == "true"

    # Plugin User Manager
    ENABLE_USER_MANAGER: bool = os.getenv("ENABLE_USER_MANAGER", "True").lower() == "true"

    # Plugin Stats
    ENABLE_STATS_PLUGIN: bool = os.getenv("ENABLE_STATS_PLUGIN", "True").lower() == "true"

    # Plugin Help
    ENABLE_HELP_PLUGIN: bool = os.getenv("ENABLE_HELP_PLUGIN", "True").lower() == "true"

    # Metrics Configuration
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", "9090"))
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"

    # Updates
    GIT_BRANCH: str = os.getenv("GIT_BRANCH", "main")

    # Supabase Configuration
    ENABLE_SUPABASE: bool = os.getenv("ENABLE_SUPABASE", "False").lower() == "true"
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")  # Anon key
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    @property
    def GEMINI_API_KEY(self) -> str:
        key = os.getenv("GEMINI_API_KEY", "")
        if key and not getattr(self, "_ai_key_logged", False):
            # Log only once to avoid spamming
            import logging

            logging.getLogger("config").info(f"🤖 AI Key detected: {key[:4]}...{key[-4:]}")
            self._ai_key_logged = True
        return key

    # Notion Integration
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")

    # Notifications (Discord/Slack)
    NOTIFICATION_WEBHOOK_URL: str = os.getenv("NOTIFICATION_WEBHOOK_URL", "")

    # SQLAlchemy URL
    # PostgreSQL es obligatorio.
    DATABASE_URL: str = field(init=False)

    def __post_init__(self):
        # Lógica de inicialización post-construcción para campos dependientes
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")

    @property
    def OPDS_AUTH(self) -> None:
        return None

    def validate(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        if not self.TELEGRAM_TOKEN:
            errors.append("TELEGRAM_TOKEN")

        # Lógica para URLs dinámicas
        if not self.BASE_URL and self.PUBLIC_DOMAIN:
            self.BASE_URL = f"https://{self.PUBLIC_DOMAIN}"

        if not self.WEBAPP_URL and self.PUBLIC_DOMAIN:
            self.WEBAPP_URL = f"https://{self.PUBLIC_DOMAIN}"

        if not self.BASE_URL:
            errors.append("BASE_URL (or PUBLIC_DOMAIN)")

        if not self.DATABASE_URL:
            errors.append("DATABASE_URL")
        elif "sqlite" in self.DATABASE_URL:
            import logging

            logging.getLogger("config").warning(
                "⚠️ Usando SQLite. Se recomienda migrar a PostgreSQL según el manifiesto."
            )

        if not self.SECRET_SEED:
            errors.append("SECRET_SEED")
        if not self.DONATION_URL:
            errors.append("DONATION_URL")

        # Optional warning for AI features
        if not self.GEMINI_API_KEY:
            # We don't block start, but AI features will be disabled
            pass

        return (len(errors) == 0, errors)

    def get_six_hour_password(self) -> str:
        """
        Genera la contraseña de 8 caracteres para el modo 'evil',
        igual al script PowerShell:
          raw = f"{seed}{Year}-{Month}-{Day}-B{block}"
        """
        now = datetime.now()
        block = now.hour // 6
        # Sin guión tras el seed, para coincidir con PowerShell
        raw = f"{self.SECRET_SEED}{now.year}-{now.month}-{now.day}-B{block}"
        sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return sha[:8]


config = BotConfig()
