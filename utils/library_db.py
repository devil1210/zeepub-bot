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
    Solo si las tablas ya existen.
    """
    _log.info("Running migrations for Postgres...")
    try:
        with engine.connect() as conn:
            def table_exists(name):
                res = conn.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{name}');"))
                return res.scalar()

            # 1. Japanese Metadata columns
            if table_exists("local_books"):
                try:
                   conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS author_jap VARCHAR(255);"))
                   conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS illustrator_jap VARCHAR(255);"))
                   conn.commit()
                   _log.info("Checked/Added Japanese columns to local_books")
                except Exception as e:
                   _log.warning(f"Error checking Japanese columns on local_books: {e}")
                   conn.rollback()

            # 2. user_levels
            if table_exists("user_levels"):
                try:
                   conn.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;"))
                   conn.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_upload_epub BOOLEAN DEFAULT FALSE;"))
                   conn.execute(text("ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS default_theme_id INTEGER;"))
                   conn.commit()
                   _log.info("Checked/Added columns to user_levels")
                except Exception as e:
                    _log.warning(f"Error checking user_levels migrations: {e}")
                    conn.rollback()

            # 3. users
            if table_exists("users"):
                try:
                   conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS can_upload_epub BOOLEAN DEFAULT FALSE;"))
                   conn.commit()
                   _log.info("Checked/Added can_upload_epub on users")
                except Exception as e:
                    _log.warning(f"Error checking users migrations: {e}")
                    conn.rollback()

            # 4. local_books edition characteristics
            if table_exists("local_books"):
                try:
                   conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"))
                   conn.execute(text("ALTER TABLE local_books ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"))
                   conn.commit()
                   _log.info("Checked/Added edition columns to local_books")
                except Exception as e:
                   _log.warning(f"Error checking edition columns on local_books: {e}")
                   conn.rollback()

            # 5. upload_books
            if table_exists("upload_books"):
                try:
                   conn.execute(text("ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"))
                   conn.execute(text("ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"))
                   conn.execute(text("ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS author_jap VARCHAR(255);"))
                   conn.execute(text("ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS illustrator_jap VARCHAR(255);"))
                   conn.commit()
                   _log.info("Checked/Added edition and Japanese columns to upload_books")
                except Exception as e:
                   _log.warning(f"Error checking upload_books migrations: {e}")
                   conn.rollback()

            # 6. download_history
            if table_exists("download_history"):
                try:
                   conn.execute(text("ALTER TABLE download_history ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"))
                   conn.execute(text("ALTER TABLE download_history ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"))
                   conn.commit()
                   _log.info("Checked/Added edition columns to download_history")
                except Exception as e:
                   _log.warning(f"Error checking edition columns on download_history: {e}")
                   conn.rollback()

            # 7. user_ratings book_hash
            if table_exists("user_ratings"):
                try:
                   conn.execute(text("ALTER TABLE user_ratings ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);"))
                   conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_ratings_book_hash ON user_ratings(book_hash);"))
                   conn.commit()
                   _log.info("Checked/Added book_hash to user_ratings")
                except Exception as e:
                    _log.warning(f"Error checking book_hash on user_ratings: {e}")
                    conn.rollback()

            # 8. user_downloads book_hash
            if table_exists("user_downloads"):
                try:
                   conn.execute(text("ALTER TABLE user_downloads ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);"))
                   conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_downloads_book_hash ON user_downloads(book_hash);"))
                   conn.commit()
                   _log.info("Checked/Added book_hash to user_downloads")
                except Exception as e:
                    _log.warning(f"Error checking book_hash on user_downloads: {e}")
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

        # Asegurar que app_themes se cree si no existe (importado en user_models)
        
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
