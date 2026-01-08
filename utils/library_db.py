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

def init_library_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    Base.metadata.create_all(engine)
    print(f"Base de datos de librería inicializada en: {DB_PATH}")

def get_session():
    """
    Retorna una nueva sesión de base de datos.
    """
    return Session()
