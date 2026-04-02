from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    print("Simulating Scanner Final Cleanup...")
    # Get the series
    series = session.execute(
        text(
            "SELECT id, series_name, series_hash, book_count FROM series_metadata WHERE series_name ILIKE '%Classroom of the Elite 2nd Year%'"
        )
    ).first()
    if series:
        s_id, s_name, s_hash, b_count = series
        print(f"Checking series: {s_name} (Hash: {s_hash[:10]}...)")

        # Count using same logic as scanner
        count_q = text("SELECT count(*) FROM local_books WHERE series_hash = :h")
        actual_count = session.execute(count_q, {"h": s_hash}).scalar()
        print(f"Actual count in DB: {actual_count}")
        print(f"Book count in Meta: {b_count}")

        if actual_count != b_count:
            print(f"Mismatch detected! Updating to {actual_count}...")
            # Simulate update
            session.execute(
                text("UPDATE series_metadata SET book_count = :c WHERE id = :id"),
                {"c": actual_count, "id": s_id},
            )
            session.commit()
            print("Update committed.")

            # Now check if it would be archived
            if actual_count == 0:
                print("Series is now empty. It WOULD be archived in a full cleanup.")
    else:
        print("Series not found.")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
