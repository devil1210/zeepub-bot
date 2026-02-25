import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
from config.config_settings import config
from core.bot import ZeePubBot

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
# Silenciar bibliotecas ruidosas
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("apscheduler").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Configurar captura de logs para la interfaz
from utils.log_manager import setup_global_logging

setup_global_logging()

# Instancia global del bot
bot = ZeePubBot()

import time

app_start_time = time.time()

# Estado de la aplicación para acceso desde rutas
app_state = {"start_time": app_start_time}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Iniciar el bot
    logger.info("Iniciando ZeePub Bot junto con la API...")

    # Pre-cargar temas en caché de forma asíncrona
    from services.theme_service import theme_service

    asyncio.create_task(theme_service.get_all_themes())

    # Run DB migrations/checks
    from utils.library_db import check_migrations

    try:
        check_migrations()
    except Exception as e:
        logger.error(f"Migration check failed: {e}")

    if config.DATABASE_URL:
        if "postgresql" in config.DATABASE_URL:
            logger.info("📦 Base de Datos: PostgreSQL (Activa)")
        else:
            logger.info(f"📦 Base de Datos: {config.DATABASE_URL.split(':', 1)[0]} (Activa)")
    else:
        logger.warning("📦 WARNING: DATABASE_URL no configurada.")
    try:
        await bot.initialize()

        # Only start the bot if initialization was successful
        if bot._initialized:
            await bot.start_async()
        else:
            logger.error("Bot no se pudo inicializar correctamente. El bot NO estará disponible.")
    except Exception as e:
        logger.error(f"Fallo crítico al iniciar el bot: {e}", exc_info=True)
        # No relanzamos para que la API pueda al menos responder con su estado de error
        # o permitir administración remota si es posible.
    # Start background URL validator (only if enabled by config)
    from utils.url_validator import start_background_validator

    # Run validator every hour by default (can be tuned via environment)
    start_background_validator()
    # Guardar el bot en app_state para acceso desde rutas
    if bot._initialized:
        app_state["bot"] = bot.app.bot
        app.state.bot_instance = bot
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

from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Cache Control Middleware
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path

    # Aggressive caching for static assets (1 year)
    if any(path.startswith(prefix) for prefix in ["/assets/", "/_next/", "/api/library/covers/", "/api/profiles/"]):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    # Short cache for HTML (1 hour, must revalidate)
    elif path.endswith(".html") or path == "/" or "." not in path.split("/")[-1]:
        response.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"
    # No cache for API endpoints
    elif path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


@app.get("/api_health")
async def health_check():
    return {"message": "ZeePub Bot API is running"}


# Importar rutas

# Validar si el plugin está activo
enable_miniapp = os.getenv("ENABLE_MINI_APP", "True").lower() == "true"

if enable_miniapp:
    # Importar rutas solo si está activo
    from api.handlers.public_routes import router as public_router
    from api.library_routes import router as library_router
    from api.miniapp_routes import router as miniapp_router
    from api.routes import router

    app.include_router(public_router, prefix="/api")
    app.include_router(router)
    app.include_router(miniapp_router)
    app.include_router(library_router)

    # Montar archivos estáticos del frontend
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    # Montar portadas de la librería local
    from utils.library_db import COVERS_DIR, PROFILES_DIR

    if os.path.exists(COVERS_DIR):
        app.mount(
            "/api/library/covers",
            StaticFiles(directory=COVERS_DIR, html=False),
            name="library_covers",
        )

    if os.path.exists(PROFILES_DIR):
        app.mount(
            "/api/profiles",
            StaticFiles(directory=PROFILES_DIR, html=False),
            name="user_profiles",
        )

    # Ruta al directorio de build del frontend (Configurable)
    # Permite cambiar entre 'web_client' (nuevo) y 'zeepub-web' (anterior)
    web_client_dir = os.getenv("WEB_CLIENT_DIR", "web_client")
    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), web_client_dir, "dist")

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

            # Next.js static export generates individual HTML files for each page
            # Try to serve the specific HTML file first
            if full_path == "":
                # Root path
                html_path = os.path.join(frontend_dist, "index.html")
            else:
                # Try exact match first (e.g., search.html for /search)
                html_path = os.path.join(frontend_dist, f"{full_path}.html")
                if not os.path.exists(html_path):
                    # Try as directory with index (e.g., search/index.html)
                    html_path = os.path.join(frontend_dist, full_path, "index.html")
                if not os.path.exists(html_path):
                    # Fallback to root index.html for client-side routing
                    html_path = os.path.join(frontend_dist, "index.html")

            if os.path.exists(html_path):
                return FileResponse(html_path)
            return {"error": "Frontend not built"}

    else:
        logger.warning(f"No se encontró el directorio {frontend_dist}. El frontend no se servirá.")

else:
    logger.info("Mini App desactivada por configuración (ENABLE_MINI_APP=False).")

    @app.get("/{full_path:path}")
    async def disabled_root(full_path: str):
        return {"message": "Mini App Service is Disabled"}
