# src/api/main_api.py
import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.core.config import settings
from src.core.db import db_manager

# Configuración de Logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Fábrica de la aplicación FastAPI para Zeepub-Nexus."""
    app = FastAPI(
        title="Zeepub Nexus API",
        version=settings.VERSION,
        docs_url="/docs" if settings.LOG_LEVEL == "DEBUG" else None
    )

    @app.on_event("startup")
    async def startup_event():
        logger.info("📡 Nexus API: Iniciando...")
        await db_manager.initialize()

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🔌 Nexus API: Cerrando...")
        await db_manager.close()

    @app.get("/api_health")
    async def health():
        """Healthcheck para Docker Compose."""
        return {"status": "ok", "version": settings.VERSION}

    # Importación diferida para evitar ciclos
    from src.api.routers.bridge_router import router as bridge_router
    from src.api.routers.status_router import router as status_router
    
    app.include_router(bridge_router)
    app.include_router(status_router)

    # Montaje de archivos estáticos (Mini App / Dashboard)
    static_path = Path(__file__).resolve().parent.parent / "static"
    os.makedirs(static_path, exist_ok=True)
    
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

    return app

# Instancia global para Uvicorn
app = create_app()
