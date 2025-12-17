import importlib
import os

import pytest
from unittest.mock import MagicMock, AsyncMock

from config.config_settings import config


def test_create_and_get_short_url(tmp_path, monkeypatch):
    # Use a temporary DB path for isolation
    db_file = tmp_path / "url_cache_test.db"
    # Ensure config points to this DB
    config.URL_CACHE_DB_PATH = str(db_file)
    # Force SQLite mode by clearing DATABASE_URL
    # We must treat config as the MagicMock it is in some contexts, but here it seems it's the real config object?
    # No, test_url_cache.py imports config from config.config_settings.
    monkeypatch.setattr(config, 'DATABASE_URL', None) # mocked config usually handles setattr fine

    # Load module directly from file to avoid importing the whole `utils` package
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("url_cache_test", os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"))
    url_cache = loader.load_module()
    
    # Initialize the database
    # If config.DATABASE_URL is a Mock/MagicMock, sqlalchemy.create_engine might fail even if passed None?
    # Reviewing failure: ValueError: not enough values to unpack (expected 3, got 0) inside create_engine 
    # This implies create_engine IS called.
    # url_cache.py calls create_engine if config.DATABASE_URL and _HAS_SQLALCHEMY
    # We set DATABASE_URL to None, so it shouldn't be called.
    # UNLESS config is a MagicMock, so bool(config.DATABASE_URL) is True (a Mock object).
    
    # We must explicitly set the property return value to None if config is a Mock
    if isinstance(config, (MagicMock, AsyncMock)):
        config.DATABASE_URL = None
    else:
        monkeypatch.setattr(config, 'DATABASE_URL', None)

    url_cache.init_db()

    url = "https://example.com/some/book.epub"
    title = "Test Book"

    h = url_cache.create_short_url(url, book_title=title)
    assert isinstance(h, str) and len(h) >= 10

    resolved = url_cache.get_url_from_hash(h)
    assert resolved == url

    # Ensure count_mappings is 1
    assert url_cache.count_mappings() == 1

    # Load a fresh module instance (simulating a restart) and verify persistence
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("url_cache_test_reload", os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"))
    new_mod = module_from_spec(spec)
    spec.loader.exec_module(new_mod)
    assert new_mod.get_url_from_hash(h) == url


def test_create_and_get_short_url_sqlalchemy(tmp_path):
    pytest.importorskip("sqlalchemy")
    # Test using DATABASE_URL (SQLAlchemy) pointing to an sqlite file
    db_file = tmp_path / "url_cache_sa.db"
    config.DATABASE_URL = f"sqlite:///{db_file}"  # use absolute path

    # Load a fresh module instance (SQLAlchemy path)
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("url_cache_sa", os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"))
    sa_mod = module_from_spec(spec)
    spec.loader.exec_module(sa_mod)

    url = "https://example.org/book2.epub"
    h = sa_mod.create_short_url(url, book_title="SA Test")
    assert isinstance(h, str) and len(h) >= 10
    assert sa_mod.get_url_from_hash(h) == url
    assert sa_mod.count_mappings() == 1
