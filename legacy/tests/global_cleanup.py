import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Config log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cleanup")

DB_URL = "postgresql://zeepub:zeepub@localhost:5432/zeepub"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    logger.info("Starting global series cleanup...")

    # 1. Recalculate counts for ALL series
    series_metadata = session.execute(
        text("SELECT id, series_name, series_hash, book_count FROM series_metadata")
    ).fetchall()
    updated_count = 0

    for s_id, s_name, s_hash, b_count in series_metadata:
        actual_count = session.execute(
            text("SELECT count(*) FROM local_books WHERE series_hash = :h"), {"h": s_hash}
        ).scalar()
        if b_count != actual_count:
            logger.info(f"Updating {s_name}: {b_count} -> {actual_count}")
            session.execute(
                text("UPDATE series_metadata SET book_count = :c WHERE id = :id"),
                {"c": actual_count, "id": s_id},
            )
            updated_count += 1

    session.commit()
    logger.info(f"Updated counts for {updated_count} series.")

    # 2. Archive and delete empty series
    empty_series = session.execute(
        text(
            "SELECT id, series_name, series_hash, author, description, tags, cover_url, book_type, publisher FROM series_metadata WHERE book_count = 0"
        )
    ).fetchall()

    if empty_series:
        logger.info(f"Found {len(empty_series)} empty series. Archiving...")
        for s in empty_series:
            s_id, s_name, s_hash, s_author, s_desc, s_tags, s_cover, s_type, s_pub = s
            logger.info(f"Archiving: {s_name}")

            # Use raw SQL to avoid model dependency issues in standalone script
            session.execute(
                text("""
                INSERT INTO archived_series (series_name, series_hash, author, description, tags, cover_url, book_type, publisher, archived_at, original_series_id)
                VALUES (:name, :hash, :author, :desc, :tags, :cover, :type, :pub, now(), :orig_id)
                ON CONFLICT (series_hash) DO NOTHING
            """),
                {
                    "name": s_name,
                    "hash": s_hash,
                    "author": s_author,
                    "desc": s_desc,
                    "tags": s_tags,
                    "cover": s_cover,
                    "type": s_type,
                    "pub": s_pub,
                    "orig_id": s_id,
                },
            )

            session.execute(text("DELETE FROM series_metadata WHERE id = :id"), {"id": s_id})

        session.commit()
        logger.info("Empty series archived and deleted.")
    else:
        logger.info("No empty series found after recount.")

except Exception as e:
    logger.error(f"Error during cleanup: {e}")
    session.rollback()
finally:
    session.close()
