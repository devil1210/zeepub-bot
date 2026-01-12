import os
import sys

import pytest
from unittest.mock import MagicMock


# Ensure we have the real config, not a mock from other tests
@pytest.fixture(autouse=True)
def ensure_real_config():
    """Remove any mock of config.config_settings left by other tests."""
    # Remove mocks from both config and config.config_settings
    for mod_name in ["config", "config.config_settings"]:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if isinstance(mod, MagicMock):
                del sys.modules[mod_name]
    # Now import the real module
    from config.config_settings import config as real_config

    # Save original DATABASE_URL and force to None for tests
    original_db_url = real_config.DATABASE_URL
    real_config.DATABASE_URL = None
    yield real_config
    # Restore original value after test
    real_config.DATABASE_URL = original_db_url


from config.config_settings import config


def test_create_and_get_short_url(tmp_path, monkeypatch):
    # Force SQLite mode by clearing DATABASE_URL BEFORE module load
    monkeypatch.setattr(config, "DATABASE_URL", None)

    # Use a temporary DB path for isolation
    db_file = tmp_path / "url_cache_test.db"
    # Ensure config points to this DB
    config.URL_CACHE_DB_PATH = str(db_file)

    # Load module directly from file to avoid importing the whole `utils` package
    from importlib.util import spec_from_file_location, module_from_spec

    spec = spec_from_file_location(
        "url_cache_test",
        os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"),
    )
    url_cache = module_from_spec(spec)
    spec.loader.exec_module(url_cache)

    # Initialize the database
    # If config.DATABASE_URL is a Mock/MagicMock, sqlalchemy.create_engine might fail even if passed None?
    # Reviewing failure: ValueError: not enough values to unpack (expected 3, got 0) inside create_engine
    # This implies create_engine IS called.
    # url_cache.py calls create_engine if config.DATABASE_URL and _HAS_SQLALCHEMY
    # Force SQLite mode by clearing DATABASE_URL
    monkeypatch.setattr(config, "DATABASE_URL", None)

    url_cache.init_db()

    url = "https://example.com/some/book.epub"
    title = "Test Book"

    h = url_cache.create_short_url(url, book_title=title)
    assert isinstance(h, str) and len(h) >= 10

    resolved = url_cache.get_url_from_hash(h)
    assert resolved == url

    # Verify that the mapping was created correctly (at least 1 mapping exists)
    assert url_cache.count_mappings() >= 1

    # Load a fresh module instance (simulating a restart) and verify persistence
    from importlib.util import spec_from_file_location, module_from_spec

    spec = spec_from_file_location(
        "url_cache_test_reload",
        os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"),
    )
    new_mod = module_from_spec(spec)
    spec.loader.exec_module(new_mod)
    assert new_mod.get_url_from_hash(h) == url


def test_create_and_get_short_url_sqlalchemy(tmp_path):
    pytest.importorskip("sqlalchemy")
    # Test using DATABASE_URL (SQLAlchemy) pointing to an sqlite file
    db_file = tmp_path / "url_cache_sa.db"

    # Save original DATABASE_URL to restore after test
    original_db_url = config.DATABASE_URL

    try:
        # Set both DATABASE_URL and URL_CACHE_DB_PATH to ensure complete isolation
        config.DATABASE_URL = f"sqlite:///{db_file}"  # use absolute path
        config.URL_CACHE_DB_PATH = str(
            tmp_path / "fallback.db"
        )  # Won't be used but ensures no sharing

        # Load a fresh module instance (SQLAlchemy path)
        from importlib.util import spec_from_file_location, module_from_spec

        spec = spec_from_file_location(
            "url_cache_sa",
            os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"),
        )
        sa_mod = module_from_spec(spec)
        spec.loader.exec_module(sa_mod)

        # Initialize the database with SQLAlchemy
        sa_mod.init_db()

        url = "https://example.org/book2.epub"
        h = sa_mod.create_short_url(url, book_title="SA Test")
        assert isinstance(h, str) and len(h) >= 10
        assert sa_mod.get_url_from_hash(h) == url
        # Verify that the mapping was created correctly (at least 1 mapping exists)
        assert sa_mod.count_mappings() >= 1
    finally:
        # Restore original DATABASE_URL
        config.DATABASE_URL = original_db_url
