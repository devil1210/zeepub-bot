from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    count = session.execute(text("SELECT count(*) FROM series_metadata")).scalar()
    print(f"Total series: {count}")

    stale_series = session.execute(
        text("""
        SELECT sm.series_name, sm.book_count 
        FROM series_metadata sm 
        LEFT JOIN local_books lb ON sm.series_hash = lb.series_hash 
        WHERE lb.id IS NULL AND sm.book_count > 0
    """)
    ).fetchall()

    print(f"Stale series (book_count > 0 but 0 books in DB): {len(stale_series)}")
    for s in stale_series:
        print(f" - {s[0]} (count: {s[1]})")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
