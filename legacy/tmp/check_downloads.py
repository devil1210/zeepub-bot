
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"

async def check_downloads():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. Check books for '5 Centimeters per Second'
    print("--- Local Books for '5 Centimeters per Second' ---")
    res = session.execute(text("SELECT id, title, series_hash, book_hash FROM local_books WHERE title ILIKE '%5 Centimeters%'"))
    books = res.fetchall()
    for book in books:
        print(f"ID: {book.id} | Title: {book.title} | SeriesHash: {book.series_hash} | BookHash: {book.book_hash}")
        
        # Count downloads for this book_hash
        dl_res = session.execute(text("SELECT count(*) FROM user_downloads WHERE book_hash = :bh"), {"bh": book.book_hash})
        dl_count = dl_res.scalar()
        print(f"  -> Downloads (book_hash): {dl_count}")
        
    # 2. Check total downloads in user_downloads
    print("\n--- Total Downloads Count ---")
    total_dl = session.execute(text("SELECT count(*) FROM user_downloads")).scalar()
    print(f"Total rows in user_downloads: {total_dl}")
    
    # 3. Check some samples
    print("\n--- Download Samples ---")
    samples = session.execute(text("SELECT id, user_id, book_hash, series_hash, title FROM user_downloads LIMIT 5")).fetchall()
    for s in samples:
        print(f"DL_ID: {s.id} | User: {s.user_id} | Title: {s.title} | B_Hash: {s.book_hash} | S_Hash: {s.series_hash}")
        
    session.close()

if __name__ == "__main__":
    asyncio.run(check_downloads())
