# src/core/config.py
import os
import logging
from typing import Set
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env específicamente desde la raíz del proyecto Zeepub-bot
# __file__ es src/core/config.py -> parent es src/core -> parent.parent es src -> parent.parent.parent es Zeepub-bot/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
dot_env_path = BASE_DIR / ".env"

if dot_env_path.exists():
    load_dotenv(dotenv_path=str(dot_env_path), override=True)
else:
    # Fallback al directorio actual por si acaso
    load_dotenv(override=True)

class NexusSettings(BaseModel):
    """
    Configuración centralizada y validada para Zeepub-Nexus.
    Extraída de docker-compose.prod-lib.yml y .env del VPS.
    """
    # API & Bot
    TELEGRAM_TOKEN: str = Field(..., alias="TELEGRAM_TOKEN")
    SECRET_SEED: str = Field("Evilpubs", alias="SECRET_SEED")
    LOG_LEVEL: str = Field("DEBUG", alias="LOG_LEVEL")
    VERSION: str = "v1.0.0-NEXUS-REBUILD"
    
    # Dominios
    BASE_URL: str = Field(..., alias="BASE_URL")
    PUBLIC_DOMAIN: str = Field(..., alias="PUBLIC_DOMAIN")
    WEBAPP_URL: str = Field("", alias="WEBAPP_URL")
    
    # Database
    # En Docker el host es 'db', en local puede ser 'localhost'
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    
    # AI (Gemini 3.1 Flash Lite)
    GEMINI_API_KEY: str | None = Field(None, alias="GEMINI_API_KEY")
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    
    # Administración
    ADMIN_USERS_RAW: str = Field("", alias="ADMIN_USERS")
    
    # Rutas (Mapeadas a Volúmenes Docker por defecto)
    LIBRARY_PATH: str = Field("/library", alias="LIBRARY_PATH")
    DATA_PATH: str = Field("/app/data", alias="DATA_PATH")
    
    @property
    def ADMIN_USERS(self) -> Set[int]:
        """Convierte lista de IDs de coma a set de enteros."""
        if not self.ADMIN_USERS_RAW:
            return set()
        return {int(x.strip()) for x in self.ADMIN_USERS_RAW.split(",") if x.strip().isdigit()}

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_postgres(cls, v: str) -> str:
        # Aseguramos el driver asíncrono
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    def validate_all(self):
        logging.info(f"✅ Nexus Config Loaded: {self.VERSION}")
        logging.info(f"📁 Library Path: {self.LIBRARY_PATH}")

# Singleton
try:
    settings = NexusSettings(
        TELEGRAM_TOKEN=os.getenv("TELEGRAM_TOKEN", ""),
        BASE_URL=os.getenv("BASE_URL", ""),
        PUBLIC_DOMAIN=os.getenv("PUBLIC_DOMAIN", ""),
        WEBAPP_URL=os.getenv("WEBAPP_URL", ""),
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        ADMIN_USERS=os.getenv("ADMIN_USERS", ""),
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY"),
        LIBRARY_PATH=os.getenv("LIBRARY_PATH", "/library"),
        DATA_PATH=os.getenv("DATA_PATH", "/app/data")
    )
    settings.validate_all()
except Exception as e:
    # No fallamos aquí para permitir que las herramientas de ayuda vean el error
    logging.error(f"❌ Error en configuración: {e}")
