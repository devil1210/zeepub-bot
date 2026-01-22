import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
import sqlite3
from models.library_models import Base
from config.config_settings import config

# Carpeta dedicada para la base de datos y adjuntos (para backups fáciles)
DB_DIR = os.path.abspath("data/library")
DB_PATH = os.path.join(DB_DIR, "library.db")
COVERS_DIR = os.path.join(DB_DIR, "covers")
THUMBNAILS_DIR = os.path.join(DB_DIR, "thumbnails")
PROFILES_DIR = os.path.join(DB_DIR, "profiles")

# Crear carpetas si no existen
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)
os.makedirs(PROFILES_DIR, exist_ok=True)

# Motor de base de datos
def create_library_engine():
    db_url = config.DATABASE_URL
    
    if db_url:
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
    else:
        # Fallback to SQLite
        return create_engine(
            f"sqlite:///{DB_PATH}", 
            echo=False, 
            connect_args={"timeout": 30}
        )

engine = create_library_engine()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def check_migrations():
    """
    Añade columnas nuevas a tablas existentes para evitar OperationalError
    durante actualizaciones en fase alpha.
    """
    import logging
    _log = logging.getLogger(__name__)

    # Solo aplica a SQLite
    # Validar driver
    is_postgres = "postgres" in engine.url.drivername
    
    if not is_postgres and engine.url.drivername != "sqlite":
        _log.info("Skipping migrations for unknown DB driver.")
        return

    if is_postgres:
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
                   _log.info("Checked/Added can_upload_epub to users")
                except Exception as e:
                    _log.warning(f"Error checking can_upload_epub on users: {e}")
                    conn.rollback()

                _log.debug("Migrations checked.")

        except Exception as e:
            _log.error(f"Postgres migration error: {e}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar si la tabla existe antes de pedir info
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='local_books'")
        if not cursor.fetchone():
            _log.info("La tabla local_books no existe aún, saltando migraciones de columnas.")
            conn.close()
            return

        cursor.execute("PRAGMA table_info(local_books)")
        existing_cols = [row[1] for row in cursor.fetchall()]

        # Mapa de columnas nuevas: (nombre, tipo)
        new_cols = [
            ("layout_by", "VARCHAR(255)"),
            ("isbn", "VARCHAR(20)"),
            ("asin", "VARCHAR(50)"),
            ("uri_id", "VARCHAR(512)"),
            ("published_at", "VARCHAR(50)"),
            ("modified_at_opf", "VARCHAR(50)"),
            ("book_type", "VARCHAR(100)"),
            ("demographics", "JSON"),
            ("epub_version", "VARCHAR(20)"),
            ("word_count", "INTEGER"),
            ("page_count", "INTEGER"),
            ("reading_time", "INTEGER"),
            ("rating_average", "FLOAT DEFAULT 0.0"),
            ("rating_count", "INTEGER DEFAULT 0"),
            ("content_hash", "VARCHAR(64)"),
            ("series_hash", "VARCHAR(64)"),
            ("spanish_title", "TEXT"),
            ("jap_title", "TEXT"),
            ("description_clean", "TEXT"),
            ("cover_original", "TEXT"),
            ("cover_high", "TEXT"),
            ("cover_medium", "TEXT"),
            ("cover_low", "TEXT"),
        ]

        # 1. Migración de columnas (local_books)
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                _log.info(f"Migración: Añadiendo columna '{col_name}' a local_books...")
                cursor.execute(
                    f"ALTER TABLE local_books ADD COLUMN {col_name} {col_type}"
                )

        # 2. Migración: Crear tabla de ratings si no existe
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (book_id) REFERENCES local_books(id)
            )
        """
        )

        # Índice para evitar votos duplicados y búsquedas rápidas
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_ratings_unique ON user_ratings(user_id, book_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ratings_book ON user_ratings(book_id)"
        )


        # 3. Fallback: Crear explícitamente tabla user_audit_logs (si falla ORM)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(64) NOT NULL,
                username VARCHAR(255),
                changed_by_id VARCHAR(64),
                changed_by_username VARCHAR(255),
                action VARCHAR(50) NOT NULL,
                field_changed VARCHAR(100),
                old_value JSON,
                new_value JSON,
                changes_summary JSON,
                ip_address VARCHAR(45),
                user_agent VARCHAR(512),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON user_audit_logs(user_id)")

        # 4. Migración: Columnas en la tabla users (photo_url, etc)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(users)")
            user_cols = [row[1] for row in cursor.fetchall()]
            
            if "photo_url" not in user_cols:
                _log.info("Migración: Añadiendo columna 'photo_url' a la tabla users...")
                cursor.execute("ALTER TABLE users ADD COLUMN photo_url TEXT")
            
            if "has_library_access" not in user_cols:
                _log.info("Migración: Añadiendo columna 'has_library_access' a la tabla users...")
                cursor.execute("ALTER TABLE users ADD COLUMN has_library_access INTEGER DEFAULT 1")
                
            if "can_request_books" not in user_cols:
                _log.info("Migración: Añadiendo columna 'can_request_books' a la tabla users...")
                cursor.execute("ALTER TABLE users ADD COLUMN can_request_books INTEGER DEFAULT 1")

            if "can_upload_epub" not in user_cols:
                _log.info("Migración: Añadiendo columna 'can_upload_epub' a la tabla users...")
                cursor.execute("ALTER TABLE users ADD COLUMN can_upload_epub INTEGER DEFAULT 0")

        # 5. Migración: user_levels
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_levels'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(user_levels)")
            level_cols = [row[1] for row in cursor.fetchall()]

            if "can_upload_epub" not in level_cols:
                _log.info("Migración: Añadiendo columna 'can_upload_epub' a la tabla user_levels...")
                cursor.execute("ALTER TABLE user_levels ADD COLUMN can_upload_epub INTEGER DEFAULT 0")

        conn.commit()
        conn.close()
    except Exception as e:
        _log.error(f"Error en migración automática: {e}")


def init_fts():
    """
    Inicializa la búsqueda de texto completo (FTS5) y los triggers de sincronización.
    """
    import logging
    _log = logging.getLogger(__name__)

    # Solo aplica a SQLite
    if engine.url.drivername != "sqlite":
        _log.info("Skiping SQLite-specific FTS initialization for non-SQLite DB.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si la tabla FTS ya existe
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='books_fts'"
        )
        exists = cursor.fetchone()

        if exists:
            # Verificar si tiene el campo nuevo 'layout_by'
            cursor.execute("PRAGMA table_info(books_fts)")
            cols = [r[1] for r in cursor.fetchall()]
            if "jap_title" not in cols:
                _log.info("Migración: FTS5 no tiene 'jap_title'. Recreando índice...")
                cursor.execute("DROP TABLE books_fts")
                cursor.execute("DROP TRIGGER IF EXISTS books_ai")
                cursor.execute("DROP TRIGGER IF EXISTS books_ad")
                cursor.execute("DROP TRIGGER IF EXISTS books_au")
                exists = False

        if not exists:
            _log.info("Inicializando búsqueda de texto completo (FTS5)...")

            # Crear tabla virtual FTS5
            # Usamos content='local_books' para una external content table (más eficiente en espacio)
            cursor.execute(
                """
                CREATE VIRTUAL TABLE books_fts USING fts5(
                    title,
                    romaji_title,
                    english_title,
                    series,
                    author,
                    illustrator,
                    translator,
                    layout_by,
                    publisher,
                    tags,
                    jap_title,
                    content='local_books',
                    content_rowid='id'
                )
            """
            )

            # Poblar inicialmente
            cursor.execute(
                """
                INSERT INTO books_fts(rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags, jap_title)
                SELECT id, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags, jap_title FROM local_books
            """
            )

            # Triggers para sincronización automática
            # INSERT
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON local_books BEGIN
                  INSERT INTO books_fts(rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags, jap_title)
                  VALUES (new.id, new.title, new.romaji_title, new.english_title, new.series, new.author, new.illustrator, new.translator, new.layout_by, new.publisher, new.tags, new.jap_title);
                END;
            """
            )

            # DELETE
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON local_books BEGIN
                  INSERT INTO books_fts(books_fts, rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags, jap_title)
                  VALUES('delete', old.id, old.title, old.romaji_title, old.english_title, old.series, old.author, old.illustrator, old.translator, old.layout_by, old.publisher, old.tags, old.jap_title);
                END;
            """
            )

            # UPDATE
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON local_books BEGIN
                  INSERT INTO books_fts(books_fts, rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags, jap_title)
                  VALUES('delete', old.id, old.title, old.romaji_title, old.english_title, old.series, old.author, old.illustrator, old.translator, old.layout_by, old.publisher, old.tags, old.jap_title);
                  INSERT INTO books_fts(rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags, jap_title)
                  VALUES (new.id, new.title, new.romaji_title, new.english_title, new.series, new.author, new.illustrator, new.translator, new.layout_by, new.publisher, new.tags, new.jap_title);
                END;
            """
            )

        conn.commit()
        conn.close()
    except Exception as e:
        _log.error(f"Error inicializando FTS5: {e}")


def init_library_db():
    """
    Inicializa la base de datos creando las tablas si no existen con chequeo de integridad.
    """
    import logging
    import sqlite3
    import shutil
    from datetime import datetime
    _log = logging.getLogger(__name__)

    _log.info(f"Probando conexión a base de datos de librería: {engine.url}")

    # --- 0. Pre-crear tablas críticas via engine ---
    try:
        if engine.url.drivername == "sqlite":
            import sqlite3
            conn = sqlite3.connect(DB_PATH, timeout=10)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(64) NOT NULL,
                    username VARCHAR(255),
                    changed_by_id VARCHAR(64),
                    changed_by_username VARCHAR(255),
                    action VARCHAR(50) NOT NULL,
                    field_changed VARCHAR(100),
                    old_value JSON,
                    new_value JSON,
                    changes_summary JSON,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(512),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON user_audit_logs(user_id)")
            conn.commit()
            conn.close()
            _log.info("Tabla user_audit_logs verificada vía SQLite directo.")
    except Exception as e:
        _log.warning(f"Error en pre-creación de audit logs: {e}")

    if engine.url.drivername == "sqlite" and os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            # Integrity check can be slow on large DBs, but malformed error is worse
            res = conn.execute("PRAGMA integrity_check;").fetchone()
            conn.close()
            
            if res[0] != "ok":
                _log.error(f"⚠️ BASE DE DATOS MALFORMADA DETECTADA: {res[0]}")
                raise sqlite3.DatabaseError("Database image is malformed")
        except Exception as e:
            _log.error(f"❌ Corrupción detectada en library.db: {e}")
            
            # Backup corrupted file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupt_backup = f"{DB_PATH}.corrupt_{timestamp}"
            try:
                shutil.move(DB_PATH, corrupt_backup)
                _log.warning(f"Se ha movido la DB corrupta a: {corrupt_backup}")
            except Exception as move_err:
                _log.error(f"No se pudo mover la DB corrupta: {move_err}")
                # If we can't move it, we might need to delete it if we want to recover
                try:
                    os.remove(DB_PATH)
                    _log.warning("DB corrupta eliminada ante imposibilidad de moverla.")
                except:
                    pass

    # --- 2. Inicialización Normal ---
    try:
        # Si el archivo es nuevo o fue borrado, forzamos que el motor se reinicie
        engine.dispose()
        
        # Importar modelos para asegurar que se registren en metadata
        import models.user_audit_models  # noqa
        import models.user_models        # noqa
        import models.library_models     # noqa

        # Verificar que los modelos estén registrados
        if not Base.metadata.tables:
            _log.warning("No se detectaron tablas registradas en Base.metadata. ¿Están importados los modelos?")
        else:
            _log.info(f"Tablas detectadas en metadata: {', '.join(Base.metadata.tables.keys())}")

        # Crear tablas
        Base.metadata.create_all(engine)
        
        if engine.url.drivername == "sqlite":
            # Configurar PRAGMAs para rendimiento (SQLite)
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("PRAGMA journal_mode=WAL"))
                conn.execute(text("PRAGMA synchronous=NORMAL"))
                conn.execute(text("PRAGMA busy_timeout=5000")) # Esperar hasta 5 segundos si está ocupada
                conn.commit()
            
        _log.info("Tablas de base de datos de librería aseguradas.")
        
        check_migrations()  # Asegurar que columnas nuevas existan
        init_fts()  # Inicializar búsqueda de texto completo
        
        _log.info(f"Base de datos de librería inicializada exitosamente en: {DB_PATH}")
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
            import logging
            logging.getLogger(__name__).error(f"Fallo en inicialización tardía de DB: {e}")
            
    return Session()
