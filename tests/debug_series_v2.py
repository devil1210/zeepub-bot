import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuración manual para el debug
# Usamos localhost porque estamos en la máquina del usuario con túnel a la DB
DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # 1. Buscar la serie
    series_query = text("SELECT id, series_name, series_hash, book_count FROM series_metadata WHERE series_name ILIKE '%Classroom of the Elite 2nd Year%'")
    series = session.execute(series_query).fetchall()
    
    results = []
    for s in series:
        s_id, s_name, s_hash, b_count = s
        
        # 2. Buscar libros asociados
        books_query = text("SELECT id, filepath, filename, book_hash FROM local_books WHERE series_hash = :h")
        books = session.execute(books_query, {"h": s_hash}).fetchall()
        
        results.append({
            "series_name": s_name,
            "series_hash": s_hash,
            "book_count_in_meta": b_count,
            "books_in_db": [{"id": b[0], "filepath": b[1], "filename": b[2], "exists_on_disk": os.path.exists(b[1])} for b in books]
        })
        
    print(json.dumps(results, indent=2))

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
