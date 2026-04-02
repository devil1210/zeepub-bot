import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

from config.config_settings import config
from core.bot import ZeePubBot
from utils.log_manager import setup_global_logging

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

setup_global_logging()

# Instancia global del bot
bot = ZeePubBot()

app_start_time = time.time()

# Estado de la aplicación para acceso desde rutas
app_state = {"start_time": app_start_time}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación:
    1. Registra handlers del bot.
    2. Inicia el bot en segundo plano.
    3. Inicializa el gestor de base de datos.
    4. Limpia recursos al apagar.
    """
    from core.db_manager_pg import pg_manager

    # 1. Inicializar DB (Prevenir errores de loop en tareas de fondo)
    try:
        await pg_manager.initialize()
        # 🟢 BLOQUEO DE SEGURIDAD: Asegurar esquema y niveles básicos antes de seguir
        from core.schema_orchestrator import schema_orchestrator

        await schema_orchestrator.initialize_schema()
    except Exception as e:
        logger.error(f"Postgres initial connection/schema failed: {e}")

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

        # 🛠️ AUTO-HEAL: Corregir integridad en segundo plano al iniciar
        from services.maintenance.orchestrator import MaintenanceOrchestrator

        asyncio.create_task(MaintenanceOrchestrator.run_tool("db_integrity"))
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

    # Close DB connections
    await pg_manager.close()


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
    return {
        "status": "online",
        "message": "ZeePub Bot API is running",
        "version": "1.0.0-stable",
    }


# Importar rutas

# Validar si el plugin está activo
enable_miniapp = os.getenv("ENABLE_MINI_APP", "True").lower() == "true"

if enable_miniapp:
    # Importar rutas solo si está activo
    from api.routes_refactored import RoutesManager
    from api.v4.router import router as v4_router

    # Initialize routes manager and register all routes (Modern Architecture)
    routes_manager = RoutesManager()
    routes_manager.register_all_routes(app)

    # v4 Router central para nuevas funcionalidades
    app.include_router(v4_router, prefix="/api")

    # ==========================================
    # Short Link Download - SIEMPRE activo con miniapp
    # Usa library_db (sync) porque LocalBook vive ahí
    # ==========================================

    from core.database import async_session
    from services.library_service import LibraryService

    # Almacén temporal en memoria para Rate Limiting
    _rate_limit_data = {}  # {ip: [timestamps]}

    @app.get("/{short_link}")
    async def short_link_download(request: Request, short_link: str):
        """Descarga segura de un libro mediante su short_link (Formato Ultra-Corto)."""
        import re

        if not short_link or not re.match(r"^[a-zA-Z0-9]{10}$", short_link):
            raise HTTPException(status_code=404)

        user_agent = request.headers.get("User-Agent", "").lower()
        blocked_bots = [
            "googlebot",
            "bingbot",
            "slurp",
            "duckduckbot",
            "baiduspider",
            "yandexbot",
            "curl",
            "python-requests",
            "wget",
        ]
        if not user_agent or any(bot in user_agent for bot in blocked_bots):
            logger.warning(f"⚠️ Bot bloqueado: {short_link} (UA: {user_agent})")
            raise HTTPException(status_code=403, detail="Acceso denegado: Bots no permitidos")

        client_ip = request.headers.get("X-Forwarded-For", request.client.host)

        async with async_session() as session:
            library_service = LibraryService(session)
            book = await library_service.get_book_by_short_link(short_link)

            if not book:
                raise HTTPException(status_code=404, detail="Libro no encontrado o enlace expirado")

            filepath = book.filepath
            if not os.path.exists(filepath):
                logger.error(f"Archivo no encontrado: {filepath}")
                raise HTTPException(status_code=404, detail="El archivo físico no está disponible")

            logger.info(f"📥 Descarga iniciada: {book.title} (IP: {client_ip})")

            return FileResponse(
                path=filepath,
                media_type="application/epub+zip",
                filename=os.path.basename(filepath),
                content_disposition_type="attachment",
            )

    # Montar archivos estáticos del frontend
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
            if full_path.startswith("api"):
                return JSONResponse(status_code=404, content={"error": "API route not found"})

            # Intentar servir el archivo estático directamente si existe (ej. assets/...)
            file_path = os.path.join(frontend_dist, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)

            # Si no es un archivo, servir index.html (esto habilita el ruteo interno de React)
            index_path = os.path.join(frontend_dist, "index.html")
            if os.path.exists(index_path):
                return FileResponse(index_path)

            return JSONResponse(status_code=404, content={"error": "Frontend not built"})

    else:
        logger.warning(f"No se encontró el directorio {frontend_dist}. El frontend no se servirá.")

else:
    logger.info("Mini App desactivada por configuración (ENABLE_MINI_APP=False).")

    @app.get("/{full_path:path}")
    async def disabled_root(full_path: str):
        return {"message": "Mini App Service is Disabled"}
