from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("Deleting empty series definitively...")
    
    # Names to target
    names = ["Classroom of the Elite 2nd Year", "Baka and Test: Summon the Beasts"]
    
    for name in names:
        # Get data for archiving
        res = session.execute(text("SELECT id, series_name, series_hash, author, description, tags, cover_url, book_type, publisher FROM series_metadata WHERE series_name = :n"), {"n": name}).first()
        if res:
            s_id, s_name, s_hash, s_author, s_desc, s_tags, s_cover, s_type, s_pub = res
            print(f"Archiving and Deleting: {s_name}")
            
            # Archive
            session.execute(text("""
                INSERT INTO archived_series (series_name, series_hash, author, description, tags, cover_url, book_type, publisher, archived_at, original_series_id)
                VALUES (:name, :hash, :author, :desc, :tags, :cover, :type, :pub, now(), :orig_id)
                ON CONFLICT (series_hash) DO NOTHING
            """), {
                "name": s_name,
                "hash": s_hash,
                "author": s_author,
                "desc": s_desc,
                "tags": s_tags,  # Tags are JSONB
                "cover": s_cover,
                "type": s_type,
                "pub": s_pub,
                "orig_id": s_id
            })
            
            # Delete
            session.execute(text("DELETE FROM series_metadata WHERE id = :id"), {"id": s_id})
            print(f"Done for {s_name}")
        else:
            print(f"Not found: {name}")
            
    session.commit()
    print("Cleanup complete.")

except Exception as e:
    print(f"Error: {e}")
    session.rollback()
finally:
    session.close()
