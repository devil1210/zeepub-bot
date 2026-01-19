import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models.library_models import Base

# Carpeta dedicada para la base de datos y adjuntos (para backups fáciles)
DB_DIR = os.path.abspath("data/library")
DB_PATH = os.path.join(DB_DIR, "library.db")
COVERS_DIR = os.path.join(DB_DIR, "covers")
THUMBNAILS_DIR = os.path.join(DB_DIR, "thumbnails")

# Crear carpetas si no existen
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

# Motor de base de datos
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def check_migrations():
    """
    Añade columnas nuevas a tablas existentes para evitar OperationalError
    durante actualizaciones en fase alpha.
    """
    import sqlite3
    import logging
    _log = logging.getLogger(__name__)

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
            ("spanish_title", "TEXT"), # Added spanish_title
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

        conn.commit()
        conn.close()
    except Exception as e:
        _log.error(f"Error en migración automática: {e}")


def init_fts():
    """
    Inicializa la búsqueda de texto completo (FTS5) y los triggers de sincronización.
    """
    import sqlite3
    import logging
    _log = logging.getLogger(__name__)

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
            if "layout_by" not in cols:
                _log.info("Migración: FTS5 no tiene 'layout_by'. Recreando índice...")
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
                    content='local_books',
                    content_rowid='id'
                )
            """
            )

            # Poblar inicialmente
            cursor.execute(
                """
                INSERT INTO books_fts(rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags)
                SELECT id, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags FROM local_books
            """
            )

            # Triggers para sincronización automática
            # INSERT
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS books_ai AFTER INSERT ON local_books BEGIN
                  INSERT INTO books_fts(rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags)
                  VALUES (new.id, new.title, new.romaji_title, new.english_title, new.series, new.author, new.illustrator, new.translator, new.layout_by, new.publisher, new.tags);
                END;
            """
            )

            # DELETE
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS books_ad AFTER DELETE ON local_books BEGIN
                  INSERT INTO books_fts(books_fts, rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags)
                  VALUES('delete', old.id, old.title, old.romaji_title, old.english_title, old.series, old.author, old.illustrator, old.translator, old.layout_by, old.publisher, old.tags);
                END;
            """
            )

            # UPDATE
            cursor.execute(
                """
                CREATE TRIGGER IF NOT EXISTS books_au AFTER UPDATE ON local_books BEGIN
                  INSERT INTO books_fts(books_fts, rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags)
                  VALUES('delete', old.id, old.title, old.romaji_title, old.english_title, old.series, old.author, old.illustrator, old.translator, old.layout_by, old.publisher, old.tags);
                  INSERT INTO books_fts(rowid, title, romaji_title, english_title, series, author, illustrator, translator, layout_by, publisher, tags)
                  VALUES (new.id, new.title, new.romaji_title, new.english_title, new.series, new.author, new.illustrator, new.translator, new.layout_by, new.publisher, new.tags);
                END;
            """
            )

        conn.commit()
        conn.close()
    except Exception as e:
        _log.error(f"Error inicializando FTS5: {e}")


def init_library_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    import logging
    _log = logging.getLogger(__name__)
    
    _log.info(f"Probando conexión a base de datos de librería: {DB_PATH}")
    
    try:
        # Si el archivo es nuevo o fue borrado, forzamos que el motor se reinicie
        # para evitar problemas con pools de conexiones obsoletos
        engine.dispose()
        
        # Verificar que los modelos estén registrados
        if not Base.metadata.tables:
            _log.warning("No se detectaron tablas registradas en Base.metadata. ¿Están importados los modelos?")
        else:
            _log.info(f"Tablas detectadas en metadata: {', '.join(Base.metadata.tables.keys())}")

        # Crear tablas
        Base.metadata.create_all(engine)
        
        # Configurar PRAGMAs para rendimiento (SQLite)
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
            conn.commit()
            
        _log.info("Tablas de base de datos de librería aseguradas.")
        
        check_migrations()  # Asegurar que columnas nuevas existan
        init_fts()  # Inicializar búsqueda de texto completo
        
        _log.info(f"Base de datos de librería inicializada exitosamente en: {DB_PATH}")
    except Exception as e:
        _log.error(f"Error crítico inicializando base de datos de librería: {e}", exc_info=True)
        raise


def get_session():
    """
    Retorna una nueva sesión de base de datos.
    """
    return Session()
