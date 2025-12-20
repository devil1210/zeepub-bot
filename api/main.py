from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.bot import ZeePubBot
import logging


# Configurar logging
from config.config_settings import config
import os

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
logger = logging.getLogger(__name__)

# Instancia global del bot
bot = ZeePubBot()

# Estado de la aplicación para acceso desde rutas
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Iniciar el bot
    logger.info("Iniciando ZeePub Bot junto con la API...")
    await bot.initialize()
    await bot.start_async()
    # Start background URL validator (only if enabled by config)
    from utils.url_validator import start_background_validator

    # Run validator every hour by default (can be tuned via environment)
    start_background_validator()
    # Guardar el bot en app_state para acceso desde rutas
    app_state["bot"] = bot.app.bot
    yield
    # Shutdown: Detener el bot
    logger.info("Deteniendo ZeePub Bot...")
    await bot.stop_async()
    from utils.url_validator import stop_background_validator

    stop_background_validator()


app = FastAPI(
    title="ZeePub Bot API",
    description="API Backend para ZeePub Mini App",
    version="1.0.0",
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a la URL del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api_health")
async def health_check():
    return {"message": "ZeePub Bot API is running"}


# Importar rutas

# Validar si el plugin está activo
enable_miniapp = os.getenv("ENABLE_MINI_APP", "True").lower() == "true"

if enable_miniapp:
    # Importar rutas solo si está activo
    from api.routes import router
    from api.miniapp_routes import router as miniapp_router

    app.include_router(router)
    app.include_router(miniapp_router)

    # Montar archivos estáticos del frontend
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Ruta al directorio de build del frontend
    frontend_dist = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "zeepub-web", "dist"
    )

    if os.path.exists(frontend_dist):
        # Mount assets folder if it exists (for compatibility)
        assets_dir = os.path.join(frontend_dist, "assets")
        if os.path.exists(assets_dir):
            app.mount(
                "/assets",
                StaticFiles(directory=assets_dir),
                name="assets",
            )
        
        # Mount _next folder for Next.js static files
        next_dir = os.path.join(frontend_dist, "_next")
        if os.path.exists(next_dir):
            app.mount(
                "/_next",
                StaticFiles(directory=next_dir),
                name="next_static",
            )

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Si es una ruta de API, dejar que FastAPI la maneje (ya definidas arriba)
            if full_path.startswith("api"):
                # Si llegamos aquí y no matcheó api routes, es 404
                return {"error": "Not found"}

            # Servir index.html para cualquier otra ruta (SPA routing)
            index_path = os.path.join(frontend_dist, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)
            return {"error": "Frontend not built"}

    else:
        logger.warning(
            f"No se encontró el directorio {frontend_dist}. El frontend no se servirá."
        )

else:
    logger.info("Mini App desactivada por configuración (ENABLE_MINI_APP=False).")

    @app.get("/{full_path:path}")
    async def disabled_root(full_path: str):
        return {"message": "Mini App Service is Disabled"}
