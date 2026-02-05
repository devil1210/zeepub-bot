from utils.library_db import get_session
from models.library_models import SeriesMetadata, LocalBook
import json

with get_session() as session:
    series = session.query(SeriesMetadata).filter(SeriesMetadata.series_name.ilike('%Classroom of the Elite 2nd Year%')).all()
    results = []
    for s in series:
        books = session.query(LocalBook).filter_by(series_hash=s.series_hash).all()
        results.append({
            "series_name": s.series_name,
            "series_hash": s.series_hash,
            "book_count": s.book_count,
            "books_in_db": [{"id": b.id, "filepath": b.filepath, "filename": b.filename} for b in books]
        })
    print(json.dumps(results, indent=2))
