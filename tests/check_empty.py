from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    empty = session.execute(
        text("SELECT count(*) FROM series_metadata WHERE book_count = 0")
    ).scalar()
    print(f"Empty series still in DB: {empty}")

    names = session.execute(
        text("SELECT series_name FROM series_metadata WHERE book_count = 0")
    ).fetchall()
    for n in names:
        print(f" - {n[0]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
