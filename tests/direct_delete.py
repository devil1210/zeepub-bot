from utils.library_db import get_session
from models.library_models import SeriesMetadata
import logging

logging.basicConfig(level=logging.INFO)

with get_session() as session:
    names = ["Classroom of the Elite 2nd Year", "Baka and Test: Summon the Beasts"]
    series = session.query(SeriesMetadata).filter(SeriesMetadata.series_name.in_(names)).all()
    for s in series:
        books_count = session.query(SeriesMetadata.book_count).filter_by(id=s.id).scalar()
        if books_count == 0:
            logging.info(f"Deleting empty series: {s.series_name}")
            session.delete(s)
    session.commit()
    print("Direct delete complete.")
