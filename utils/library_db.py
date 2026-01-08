import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models.library_models import Base, LibrarySource

# Carpeta dedicada para la base de datos y adjuntos (para backups fáciles)
DB_DIR = os.path.abspath("data/library")
DB_PATH = os.path.join(DB_DIR, "library.db")
COVERS_DIR = os.path.join(DB_DIR, "covers")

# Crear carpetas si no existen
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

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
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(local_books)")
        existing_cols = [row[1] for row in cursor.fetchall()]
        
        # Mapa de columnas nuevas: (nombre, tipo)
        new_cols = [
            ('layout_by', 'VARCHAR(255)'),
            ('isbn', 'VARCHAR(20)'),
            ('asin', 'VARCHAR(50)'),
            ('uri_id', 'VARCHAR(512)'),
            ('published_at', 'VARCHAR(50)'),
            ('modified_at_opf', 'VARCHAR(50)'),
            ('book_type', 'VARCHAR(100)'),
            ('demographics', 'JSON'),
            ('epub_version', 'VARCHAR(20)'),
            ('word_count', 'INTEGER'),
            ('page_count', 'INTEGER'),
            ('reading_time', 'INTEGER')
        ]
        
        for col_name, col_type in new_cols:
            if col_name not in existing_cols:
                print(f"Migración: Añadiendo columna '{col_name}' a local_books...")
                cursor.execute(f"ALTER TABLE local_books ADD COLUMN {col_name} {col_type}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error en migración automática: {e}")

def init_library_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    Base.metadata.create_all(engine)
    check_migrations() # Asegurar que columnas nuevas existan
    print(f"Base de datos de librería inicializada en: {DB_PATH}")

def get_session():
    """
    Retorna una nueva sesión de base de datos.
    """
    return Session()
