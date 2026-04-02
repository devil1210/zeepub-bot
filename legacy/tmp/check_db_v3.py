
import asyncio
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

DATABASE_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

def check_db():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("--- 1. Top 5 Books with Downloads (Joining local_books and user_downloads) ---")
    query = text("""
        SELECT b.title, b.book_hash, count(d.id) as dl_count 
        FROM local_books b
        LEFT JOIN user_downloads d ON d.book_hash = b.book_hash
        GROUP BY b.id, b.title, b.book_hash
        HAVING count(d.id) > 0
        ORDER BY dl_count DESC
        LIMIT 10;
    """)
    res = session.execute(query).fetchall()
    for r in res:
        print(f"Title: {r.title} | Hash: {r.book_hash} | Downloads: {r.dl_count}")

    print("\n--- 2. Downloads without book_hash match ---")
    query_unmatched = text("""
        SELECT d.title, d.book_hash, count(*) 
        FROM user_downloads d
        LEFT JOIN local_books b ON d.book_hash = b.book_hash
        WHERE b.id IS NULL
        GROUP BY d.book_hash, d.title
        LIMIT 10;
    """)
    res_unmatched = session.execute(query_unmatched).fetchall()
    for r in res_unmatched:
        print(f"Title: {r.title} | Hash: {r.book_hash} | Count: {r.count}")

    session.close()

if __name__ == "__main__":
    check_db()
