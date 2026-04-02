
from sqlalchemy import create_engine, text
DATABASE_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    res = conn.execute(text("SELECT series_hash FROM local_books WHERE book_hash = 'c6736ebe43df33d358da176287cebe66f640f04de597f2f6b4f01775f8c5ed56'"))
    row = res.fetchone()
    if row:
        print(row.series_hash)
