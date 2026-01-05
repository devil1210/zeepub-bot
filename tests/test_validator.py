import asyncio
import importlib.util
import os
import sys
import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture
def mock_url_cache(tmp_path, monkeypatch):
    from config.config_settings import config
    monkeypatch.setattr(config, 'DATABASE_URL', None)
    db_file = tmp_path / "url_cache_validator.db"
    monkeypatch.setattr(config, 'URL_CACHE_DB_PATH', str(db_file))

    # Load module directly
    spec = importlib.util.spec_from_file_location("url_cache_mod", os.path.join(os.path.dirname(__file__), "..", "utils", "url_cache.py"))
    url_cache = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(url_cache)
    url_cache.init_db()

    # Patch sys.modules for duration of test
    with patch.dict(sys.modules, {'utils.url_cache': url_cache}):
        yield url_cache

@pytest.mark.asyncio
async def test_get_candidates_and_validator(mock_url_cache, monkeypatch):
    url_cache = mock_url_cache
    h1 = url_cache.create_short_url("https://example.com/one.epub", book_title="one")
    h2 = url_cache.create_short_url("https://example.com/two.epub", book_title="two")

    conn = url_cache._get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE url_mappings SET is_valid = 0 WHERE hash = ?", (h2,))
    conn.commit()
    conn.close()

    c = url_cache.get_candidates_for_validation(limit=10, older_than_seconds=1)
    assert any(h2 == x[0] for x in c)

    spec2 = importlib.util.spec_from_file_location("utils.url_validator", os.path.join(os.path.dirname(__file__), "..", "utils", "url_validator.py"))
    url_validator = importlib.util.module_from_spec(spec2)

    with patch.dict(sys.modules, {'utils.url_validator': url_validator}):
        spec2.loader.exec_module(url_validator)
        loop = asyncio.get_event_loop()
        task = url_validator.start_background_validator(loop=loop, interval=1, batch_size=5)
        # Smoke test: give it a bit of time
        await asyncio.sleep(0.1)
        url_validator.stop_background_validator()
        assert task is not None
