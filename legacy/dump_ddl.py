from sqlalchemy import create_mock_engine
from models.base import Base
from models.library_models import LibrarySource, Series, Book
from models.user_models import User, UserLevel, DownloadLog

def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))

engine = create_mock_engine("postgresql://", dump)
Base.metadata.create_all(engine)
