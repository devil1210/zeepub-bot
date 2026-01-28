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

    return create_engine(db_url, echo=False, pool_pre_ping=True)


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
                res = conn.execute(
                    text(
                        f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{name}');"
                    )
                )
                return res.scalar()

            # 0. Table series_metadata (Must exist before FK)
            try:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS series_metadata (
                        id SERIAL PRIMARY KEY,
                        series_name VARCHAR(255) NOT NULL,
                        series_spanish VARCHAR(255),
                        series_hash VARCHAR(64) UNIQUE NOT NULL,
                        author VARCHAR(255),
                        author_jap VARCHAR(255),
                        illustrator VARCHAR(255),
                        illustrator_jap VARCHAR(255),
                        description TEXT,
                        tags JSONB,
                        cover_url VARCHAR(1024),
                        book_count INTEGER DEFAULT 0,
                        book_type VARCHAR(100),
                        publisher VARCHAR(255),
                        rating_average FLOAT DEFAULT 0.0,
                        rating_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                    );
                """)
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_series_metadata_hash ON series_metadata(series_hash);"
                    )
                )
                conn.commit()
            except Exception as e:
                _log.warning(f"Error creating series_metadata table: {e}")
                conn.rollback()

            # 0.1 Table admins
            try:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS admins (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL UNIQUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
                    );
                """)
                )
                conn.commit()
            except Exception as e:
                _log.warning(f"Error creating admins table: {e}")
                conn.rollback()

            # 0.2 Table metadata_proposals
            try:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS metadata_proposals (
                        id SERIAL PRIMARY KEY,
                        series_hash VARCHAR(64) NOT NULL,
                        proposal_data JSONB NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
                        processed_at TIMESTAMP WITH TIME ZONE
                    );
                """)
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_metadata_proposals_hash ON metadata_proposals(series_hash);"
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_metadata_proposals_status ON metadata_proposals(status);"
                    )
                )
                conn.commit()
            except Exception as e:
                _log.warning(f"Error creating metadata_proposals table: {e}")
                conn.rollback()

            # 0.3 Tables for archiving deleted content
            try:
                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS archived_series (
                        id SERIAL PRIMARY KEY,
                        series_name VARCHAR(255) NOT NULL,
                        series_spanish VARCHAR(255),
                        series_hash VARCHAR(64) UNIQUE NOT NULL,
                        author VARCHAR(255),
                        description TEXT,
                        tags JSONB,
                        cover_url VARCHAR(1024),
                        book_type VARCHAR(100),
                        publisher VARCHAR(255),
                        archived_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
                        original_series_id INTEGER
                    );
                """)
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_archived_series_hash ON archived_series(series_hash);"
                    )
                )

                conn.execute(
                    text("""
                    CREATE TABLE IF NOT EXISTS archived_books (
                        id SERIAL PRIMARY KEY,
                        series_hash VARCHAR(64),
                        book_hash VARCHAR(64),
                        title VARCHAR(512) NOT NULL,
                        filename VARCHAR(512),
                        last_filepath VARCHAR(1024),
                        volume FLOAT,
                        author VARCHAR(255),
                        book_type VARCHAR(100),
                        archived_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
                        original_book_id INTEGER,
                        reason VARCHAR(255)
                    );
                """)
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_archived_books_hash ON archived_books(book_hash);"
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS idx_archived_books_series ON archived_books(series_hash);"
                    )
                )
                conn.commit()
            except Exception as e:
                _log.warning(f"Error creating archiving tables: {e}")
                conn.rollback()

            # 0.4 SeriesMetadata Migrations (Columns added later)
            if table_exists("series_metadata"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS series_spanish VARCHAR(255);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS book_type VARCHAR(100);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS publisher VARCHAR(255);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE series_metadata ADD COLUMN IF NOT EXISTS demographics JSONB;"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added columns to series_metadata")
                except Exception as e:
                    _log.warning(f"Error checking series_metadata migrations: {e}")
                    conn.rollback()

            # 1. Metadata and Title variants
            if table_exists("local_books"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS author_jap VARCHAR(255);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS illustrator_jap VARCHAR(255);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS romaji_title VARCHAR(512);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS spanish_title VARCHAR(512);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS english_title VARCHAR(512);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS jap_title VARCHAR(512);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS series_spanish VARCHAR(255);"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added Metadata and Title columns to local_books")
                except Exception as e:
                    _log.warning(f"Error checking Metadata/Title columns on local_books: {e}")
                    conn.rollback()

            # 2. user_levels
            if table_exists("user_levels"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS allow_theme_templates BOOLEAN DEFAULT FALSE;"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_upload_epub BOOLEAN DEFAULT FALSE;"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS default_theme_id INTEGER;"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added columns to user_levels")
                except Exception as e:
                    _log.warning(f"Error checking user_levels migrations: {e}")
                    conn.rollback()

            # 3. users
            if table_exists("users"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE users ADD COLUMN IF NOT EXISTS can_upload_epub BOOLEAN DEFAULT FALSE;"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added can_upload_epub on users")
                except Exception as e:
                    _log.warning(f"Error checking users migrations: {e}")
                    conn.rollback()

            # 4. local_books edition characteristics, optimized series & covers
            if table_exists("local_books"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS series_metadata_id INTEGER REFERENCES series_metadata(id);"
                        )
                    )

                    # Cover Quality columns
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS cover_original VARCHAR(1024);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS cover_high VARCHAR(1024);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS cover_medium VARCHAR(1024);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS cover_low VARCHAR(1024);"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE local_books ADD COLUMN IF NOT EXISTS summary VARCHAR(1024);"
                        )
                    )

                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_local_books_series_metadata_id ON local_books(series_metadata_id);"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added edition, series and cover columns to local_books")
                except Exception as e:
                    _log.warning(f"Error checking edition/series/cover columns on local_books: {e}")
                    conn.rollback()

            # 5. upload_books
            if table_exists("upload_books"):
                try:
                    # Ensure ALL potential columns exist for upload_books
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
                        conn.execute(
                            text(
                                f"ALTER TABLE upload_books ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
                            )
                        )

                    conn.commit()
                    _log.info("Checked/Added all required columns to upload_books")
                except Exception as e:
                    _log.warning(f"Error checking upload_books migrations: {e}")
                    conn.rollback()

            # 6. download_history
            if table_exists("download_history"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE download_history ADD COLUMN IF NOT EXISTS is_uncensored INTEGER DEFAULT 0;"
                        )
                    )
                    conn.execute(
                        text(
                            "ALTER TABLE download_history ADD COLUMN IF NOT EXISTS color_mode VARCHAR(50);"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added edition columns to download_history")
                except Exception as e:
                    _log.warning(f"Error checking edition columns on download_history: {e}")
                    conn.rollback()

            # 7. user_ratings book_hash
            if table_exists("user_ratings"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE user_ratings ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);"
                        )
                    )
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_user_ratings_book_hash ON user_ratings(book_hash);"
                        )
                    )
                    conn.commit()
                    _log.info("Checked/Added book_hash to user_ratings")
                except Exception as e:
                    _log.warning(f"Error checking book_hash on user_ratings: {e}")
                    conn.rollback()

            # 8. user_downloads book_hash
            if table_exists("user_downloads"):
                try:
                    conn.execute(
                        text(
                            "ALTER TABLE user_downloads ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);"
                        )
                    )
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS idx_user_downloads_book_hash ON user_downloads(book_hash);"
                        )
                    )
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
        import models.user_models  # noqa
        import models.library_models  # noqa
        import models.download_models  # noqa

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
