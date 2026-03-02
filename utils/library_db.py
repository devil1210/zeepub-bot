import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from config.config_settings import config
from models.library_models import Base

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

    # Fallback 'db' to 'localhost' if running outside Docker (common for local agents)
    # Testing host 'db' reaches vs 'localhost'
    if "@db:" in db_url and os.name == "nt":
        # Simple hack for local agent on Windows reaching Docker Postgres
        db_url = db_url.replace("@db:", "@localhost:", 1)
        _log.debug("Converting 'db' to 'localhost' for Windows local execution.")

    # Configuración de pool optimizada para producción
    # Eliminamos connect_timeout que causa problemas en algunas versiones del driver
    return create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_timeout=30,
        connect_args={
            "options": "-c statement_timeout=30000",  # Sigue permitiendo timeout de query
        },
    )


engine = create_library_engine()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def check_migrations():
    """
    Añade columnas nuevas a tablas existentes en PostgreSQL.
    Solo si las tablas ya existen.
    """
    _log.debug(f"Running migrations for {engine.dialect.name}...")
    try:
        with engine.connect() as conn:

            def table_exists(name):
                res = conn.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{name}');")
                )
                return res.scalar()

            def column_exists(table, column):
                res = conn.execute(
                    text(
                        f"SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column}');"
                    )
                )
                return res.scalar()

            def add_column_if_missing(table, column, col_type):
                if not column_exists(table, column):
                    _log.info(f"Adding column {column} to {table}...")
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};"))
                        conn.commit()
                    except Exception as e:
                        _log.warning(f"Could not add column {column} to {table}: {e}")
                        conn.rollback()

            # 0. Table series_metadata
            try:
                if not table_exists("series_metadata"):
                    _log.info("Creating series_metadata table...")
                    # Manual create to ensure structure if metadata.create_all missed it
                    conn.execute(
                        text("""
                        CREATE TABLE series_metadata (
                            id SERIAL PRIMARY KEY,
                            series_name VARCHAR(255) NOT NULL,
                            series_spanish VARCHAR(255),
                            series_hash VARCHAR(64) UNIQUE NOT NULL,
                            author VARCHAR(255),
                            description TEXT,
                            cover_url VARCHAR(1024),
                            book_count INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                        );
                    """)
                    )
                    conn.commit()

                # Check for additional columns in series_metadata
                add_column_if_missing("series_metadata", "series_spanish", "VARCHAR(255)")
                add_column_if_missing("series_metadata", "book_type", "VARCHAR(100)")
                add_column_if_missing("series_metadata", "publisher", "VARCHAR(255)")
                add_column_if_missing("series_metadata", "demographics", "JSONB")
                add_column_if_missing("series_metadata", "slug", "VARCHAR(100)")
                add_column_if_missing("series_metadata", "rating_average", "FLOAT DEFAULT 0.0")

                # Check for publication_templates additions
                add_column_if_missing("publication_templates", "is_default", "BOOLEAN DEFAULT FALSE")
                add_column_if_missing("publication_templates", "extra_config", "JSONB")
                add_column_if_missing("series_metadata", "rating_count", "INTEGER DEFAULT 0")

                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_series_metadata_hash ON series_metadata(series_hash);")
                )
                conn.commit()
            except Exception as e:
                _log.warning(f"Error migrating series_metadata: {e}")
                conn.rollback()

            # 1. local_books columns
            if table_exists("local_books"):
                add_column_if_missing("local_books", "author_jap", "VARCHAR(255)")
                add_column_if_missing("local_books", "illustrator_jap", "VARCHAR(255)")
                add_column_if_missing("local_books", "romaji_title", "VARCHAR(512)")
                add_column_if_missing("local_books", "spanish_title", "VARCHAR(512)")
                add_column_if_missing("local_books", "english_title", "VARCHAR(512)")
                add_column_if_missing("local_books", "jap_title", "VARCHAR(512)")
                add_column_if_missing("local_books", "series_spanish", "VARCHAR(255)")
                add_column_if_missing("local_books", "series_english", "VARCHAR(255)")
                add_column_if_missing("local_books", "is_uncensored", "INTEGER DEFAULT 0")
                add_column_if_missing("local_books", "color_mode", "VARCHAR(50)")
                add_column_if_missing("local_books", "series_metadata_id", "INTEGER")
                add_column_if_missing("local_books", "cover_original", "VARCHAR(1024)")
                add_column_if_missing("local_books", "cover_high", "VARCHAR(1024)")
                add_column_if_missing("local_books", "cover_medium", "VARCHAR(1024)")
                add_column_if_missing("local_books", "cover_low", "VARCHAR(1024)")
                add_column_if_missing("local_books", "summary", "VARCHAR(1024)")
                add_column_if_missing("local_books", "demographics", "JSONB")
                add_column_if_missing("local_books", "short_link", "VARCHAR(20) UNIQUE")

            # 2. user_levels
            if table_exists("user_levels"):
                add_column_if_missing("user_levels", "allow_theme_templates", "BOOLEAN DEFAULT FALSE")
                add_column_if_missing("user_levels", "can_upload_epub", "BOOLEAN DEFAULT FALSE")
                add_column_if_missing("user_levels", "default_theme_id", "INTEGER")
                add_column_if_missing("user_levels", "show_recommendations", "BOOLEAN DEFAULT TRUE")

            # 3. users
            if table_exists("users"):
                add_column_if_missing("users", "can_upload_epub", "BOOLEAN DEFAULT FALSE")

            # 4. upload_books
            if table_exists("upload_books"):
                cols = [
                    ("illustrator", "VARCHAR(255)"),
                    ("translator", "VARCHAR(255)"),
                    ("layout_by", "VARCHAR(255)"),
                    ("author_jap", "VARCHAR(255)"),
                    ("illustrator_jap", "VARCHAR(255)"),
                    ("is_uncensored", "INTEGER DEFAULT 0"),
                    ("color_mode", "VARCHAR(50)"),
                    ("book_hash", "VARCHAR(64)"),
                    ("series_hash", "VARCHAR(64)"),
                    ("identity_match", "VARCHAR(10) DEFAULT 'False'"),
                    ("path_collision", "VARCHAR(10) DEFAULT 'False'"),
                    ("processed", "VARCHAR(10) DEFAULT 'False'"),
                    ("series_spanish", "VARCHAR(255)"),
                    ("upload_metadata", "JSONB"),
                ]
                for col_name, col_type in cols:
                    add_column_if_missing("upload_books", col_name, col_type)

            # 5. download_history
            if table_exists("download_history"):
                add_column_if_missing("download_history", "is_uncensored", "INTEGER DEFAULT 0")
                add_column_if_missing("download_history", "color_mode", "VARCHAR(50)")

            # 6. user_ratings book_hash
            if table_exists("user_ratings"):
                add_column_if_missing("user_ratings", "book_hash", "VARCHAR(64)")
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_ratings_book_hash ON user_ratings(book_hash);"))
                conn.commit()

            # 7. user_downloads book_hash
            if table_exists("user_downloads"):
                add_column_if_missing("user_downloads", "book_hash", "VARCHAR(64)")
                conn.execute(
                    text("CREATE INDEX IF NOT EXISTS idx_user_downloads_book_hash ON user_downloads(book_hash);")
                )
                conn.commit()

            # 8. archived_series columns
            if table_exists("archived_series"):
                add_column_if_missing("archived_series", "spanish_title", "VARCHAR(255)")
                add_column_if_missing("archived_series", "book_type", "VARCHAR(100)")
                add_column_if_missing("archived_series", "publisher", "VARCHAR(255)")

            # 9. archived_books columns
            if table_exists("archived_books"):
                add_column_if_missing("archived_books", "author", "VARCHAR(255)")
                add_column_if_missing("archived_books", "book_type", "VARCHAR(100)")

            # 10. ai_learning_feedback columns
            if table_exists("ai_learning_feedback"):
                add_column_if_missing("ai_learning_feedback", "proposed_spanish", "VARCHAR")
                add_column_if_missing("ai_learning_feedback", "final_spanish", "VARCHAR")

            _log.debug(f"Migrations for {engine.dialect.name} completed.")

    except Exception as e:
        _log.error(f"Postgres migration error: {e}")


def init_library_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    _log.debug(f"Probando conexión a base de datos de librería: {engine.url}")

    try:
        # Importar modelos para asegurar que se registren en metadata
        import models.user_audit_models  # noqa
        import models.user_models  # noqa
        import models.library_models  # noqa
        import models.download_models  # noqa
        import models.publication_models  # noqa
        import models.agent_models  # noqa

        # Asegurar que app_themes se cree si no existe (importado en user_models)

        # Crear tablas
        Base.metadata.create_all(engine)

        _log.debug("Tablas de base de datos de librería aseguradas.")

        check_migrations()

    except Exception as e:
        _log.error(f"Error crítico inicializando base de datos de librería: {e}", exc_info=True)
        raise


import threading

_lib_db_lock = threading.Lock()
_lib_db_initialized = False


def get_session():
    """
    Retorna una nueva sesión de base de datos.
    Asegura que la DB esté inicializada al menos una vez por proceso (Thread-safe).
    """
    global _lib_db_initialized
    if not _lib_db_initialized:
        with _lib_db_lock:
            # Re-check inside lock (Double-Checked Locking pattern)
            if not _lib_db_initialized:
                try:
                    init_library_db()
                    _lib_db_initialized = True
                except Exception as e:
                    _log.error(f"Fallo en inicialización tardía de DB: {e}")

    return Session()
