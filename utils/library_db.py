import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from models.library_models import Base
from config.config_settings import config

_log = logging.getLogger(__name__)

# Carpetas para adjuntos
DB_DIR = os.path.abspath("data/library")
COVERS_DIR = os.path.join(DB_DIR, "covers")
THUMBNAILS_DIR = os.path.join(DB_DIR, "thumbnails")
PROFILES_DIR = os.path.join(DB_DIR, "profiles")

# Crear carpetas si no existen
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)

def create_library_engine():
    db_url = config.DATABASE_URL
    
    if not db_url:
        _log.error("DATABASE_URL no está configurada. PostgreSQL es obligatorio.")
        raise RuntimeError("DATABASE_URL is required for PostgreSQL operation.")

    # For synchronous SQLAlchemy (psycopg2), ensure url starts with postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # If it's the async url, convert back to sync for this module
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "", 1)
        
    return create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True
    )

engine = create_library_engine()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def check_migrations():
    """
    Añade columnas nuevas a tablas existentes en PostgreSQL.
    """
    _log.info("Running migrations for Postgres...")
    try:
        with engine.connect() as conn:
            # 1. local_books.description_clean
            try:
               conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS description_clean VARCHAR(5000);"))
               conn.commit()
               _log.info("Checked/Added description_clean to local_books")
            except Exception as e:
               _log.warning(f"Error checking description_clean: {e}")
               conn.rollback()

            # 2. user_levels.allow_theme_templates
            try:
               conn.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;"))
               conn.commit()
               _log.info("Checked/Added allow_theme_templates to user_levels")
            except Exception as e:
                _log.warning(f"Error checking allow_theme_templates: {e}")
                conn.rollback()

            # 3. user_levels.can_upload_epub
            try:
               conn.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_upload_epub BOOLEAN DEFAULT FALSE;"))
               conn.commit()
               _log.info("Checked/Added can_upload_epub to user_levels")
            except Exception as e:
                _log.warning(f"Error checking can_upload_epub on user_levels: {e}")
                conn.rollback()

            # 4. users.can_upload_epub
            try:
               conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS can_upload_epub BOOLEAN DEFAULT FALSE;"))
               conn.commit()
               _log.info("Checked/Added can_upload_epub on users")
            except Exception as e:
                _log.warning(f"Error checking can_upload_epub on users: {e}")
                conn.rollback()

            # 5. local_books edition characteristics
            try:
               conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"))
               conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"))
               conn.commit()
               _log.info("Checked/Added edition columns to local_books")
            except Exception as e:
               _log.warning(f"Error checking edition columns on local_books: {e}")
               conn.rollback()

            # 6. upload_books edition characteristics
            try:
               conn.execute(text("ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"))
               conn.execute(text("ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"))
               conn.commit()
               _log.info("Checked/Added edition columns to upload_books")
            except Exception as e:
               _log.warning(f"Error checking edition columns on upload_books: {e}")
               conn.rollback()

            # 7. download_history edition characteristics
            try:
               conn.execute(text("ALTER TABLE download_history ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"))
               conn.execute(text("ALTER TABLE download_history ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"))
               conn.commit()
               _log.info("Checked/Added edition columns to download_history")
            except Exception as e:
               _log.warning(f"Error checking edition columns on download_history: {e}")
               conn.rollback()

            _log.debug("Migrations checked.")

    except Exception as e:
        _log.error(f"Postgres migration error: {e}")

def init_library_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    _log.info(f"Probando conexión a base de datos de librería: {engine.url}")

    try:
        # Importar modelos para asegurar que se registren en metadata
        import models.user_audit_models  # noqa
        import models.user_models        # noqa
        import models.library_models     # noqa
        import models.download_models    # noqa

        # Crear tablas
        Base.metadata.create_all(engine)
        
        _log.info("Tablas de base de datos de librería aseguradas.")
        
        check_migrations()
        
    except Exception as e:
        _log.error(f"Error crítico inicializando base de datos de librería: {e}", exc_info=True)
        raise

_lib_db_initialized = False

def get_session():
    """
    Retorna una nueva sesión de base de datos.
    Asegura que la DB esté inicializada al menos una vez por proceso.
    """
    global _lib_db_initialized
    if not _lib_db_initialized:
        try:
            init_library_db()
            _lib_db_initialized = True
        except Exception as e:
            _log.error(f"Fallo en inicialización tardía de DB: {e}")
            
    return Session()
