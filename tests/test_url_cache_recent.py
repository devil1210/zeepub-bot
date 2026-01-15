import importlib.util
import os
import sys
import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def ensure_real_config():
    """Remove any mock of config.config_settings left by other tests."""
    for mod_name in ["config", "config.config_settings"]:
        if mod_name in sys.modules:
            mod = sys.modules[mod_name]
            if isinstance(mod, MagicMock):
                del sys.modules[mod_name]
    from config.config_settings import config as real_config

    original_db_url = real_config.DATABASE_URL
    real_config.DATABASE_URL = None
    yield real_config
    real_config.DATABASE_URL = original_db_url


from config.config_settings import config


def test_get_recent_links(tmp_path):
    # Force SQLite mode BEFORE module load
    config.DATABASE_URL = None

    db_file = tmp_path / "url_cache_recent.db"
    config.URL_CACHE_DB_PATH = str(db_file)

    spec = importlib.util.spec_from_file_location(
        "uc", os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py")
    )
    uc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(uc)

    # Init DB
    uc.init_db()

    # Create some mappings
    hashes = []
    for i in range(5):
        h = uc.create_short_url(
            f"https://example.com/book{i}.epub", book_title=f"book{i}"
        )
        hashes.append(h)

    recent = uc.get_recent_links(limit=3)
    assert len(recent) == 3
    # Ensure returned entries look correct and include at least one of our created URLs
    assert len(recent) == 3
    returned_urls = [r[1] for r in recent]
    # At least one of our created URLs should appear among the recent results
    assert any(
        u in [f"https://example.com/book{i}.epub" for i in range(5)]
        for u in returned_urls
    )
