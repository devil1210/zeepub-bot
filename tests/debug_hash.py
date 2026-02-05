from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Check hashes
    res = session.execute(text("SELECT series_hash, series_name FROM series_metadata WHERE series_name ILIKE '%Classroom of the Elite 2nd Year%'")).first()
    if res:
        s_hash, s_name = res
        print(f"Series: {s_name}")
        print(f"Hash in Metadata: {s_hash}")
        
        # Check books in archive
        archived = session.execute(text("SELECT book_hash, title, series_hash FROM archived_books WHERE series_hash = :h"), {"h": s_hash}).fetchall()
        print(f"Archived books for this hash: {len(archived)}")
        for i, a in enumerate(archived):
            print(f"  {i+1}. {a[1]} (Hash: {a[2]})")
            
        # Check total books for this hash
        current = session.execute(text("SELECT count(*) FROM local_books WHERE series_hash = :h"), {"h": s_hash}).scalar()
        print(f"Current books for this hash: {current}")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
