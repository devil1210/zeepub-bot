import sys
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

# Mock ZeePubBot BEFORE importing api.main
mock_bot_module = MagicMock()
sys.modules["core.bot"] = mock_bot_module
mock_bot_class = MagicMock()
mock_bot_module.ZeePubBot = mock_bot_class
mock_bot_instance = MagicMock()
mock_bot_class.return_value = mock_bot_instance
mock_bot_instance.initialize = AsyncMock()
mock_bot_instance.start_async = AsyncMock()
mock_bot_instance.stop_async = AsyncMock()

from api.main import app
from config.config_settings import config

client = TestClient(app)

@pytest.fixture
def mock_opds_roots(monkeypatch):
    monkeypatch.setattr(config, "OPDS_ROOT_START_SUFFIX", "/start")
    monkeypatch.setattr(config, "OPDS_ROOT_EVIL_SUFFIX", "/evil")
    monkeypatch.setattr(config, "OPDS_SERVER_URL", "http://opds.test")
    monkeypatch.setattr(config, "ADMIN_USERS", {123})
    monkeypatch.setattr(config, "VIP_LIST", {456})
    monkeypatch.setattr(config, "PREMIUM_LIST", {789})
    monkeypatch.setattr(config, "WHITELIST", {111})

def test_role_based_access_admin(mock_opds_roots, monkeypatch):
    mock_feed = AsyncMock()
    mock_feed_obj = MagicMock()
    mock_feed_obj.feed.title = "Evil Root"
    mock_feed_obj.entries = []
    mock_feed.return_value = mock_feed_obj
    monkeypatch.setattr("api.routes.get_cached_feed", mock_feed)

    response = client.get("/api/feed?uid=123")
    assert response.status_code == 200
    assert response.json()["title"] == "Evil Root"
    mock_feed.assert_called_with("http://opds.test/evil")

def test_role_based_access_vip(mock_opds_roots, monkeypatch):
    mock_feed = AsyncMock()
    mock_feed_obj = MagicMock()
    mock_feed_obj.feed.title = "Start Root"
    mock_feed_obj.entries = []
    mock_feed.return_value = mock_feed_obj
    monkeypatch.setattr("api.routes.get_cached_feed", mock_feed)

    response = client.get("/api/feed?uid=456")
    assert response.status_code == 200
    assert response.json()["title"] == "Start Root"
    mock_feed.assert_called_with("http://opds.test/start")

def test_role_based_access_whitelist(mock_opds_roots, monkeypatch):
    mock_feed = AsyncMock()
    mock_feed_obj = MagicMock()
    mock_feed_obj.feed.title = "Start Root"
    mock_feed_obj.entries = []
    mock_feed.return_value = mock_feed_obj
    monkeypatch.setattr("api.routes.get_cached_feed", mock_feed)

    response = client.get("/api/feed?uid=111")
    assert response.status_code == 200
    assert response.json()["title"] == "Start Root"
    mock_feed.assert_called_with("http://opds.test/start")

def test_role_based_access_denied(mock_opds_roots):
    response = client.get("/api/feed?uid=999")
    assert response.status_code == 403
    assert "restringido" in response.json()["detail"]

def test_book_detail_parsing(monkeypatch):
    mock_feed = AsyncMock()
    
    # Mock single-entry feed (where entry is in feed.feed)
    mock_feed_obj = MagicMock()
    mock_feed_obj.entries = []
    mock_feed_obj.feed.title = "Test Book"
    mock_feed_obj.feed.links = [
        {"rel": "self", "href": "http://opds.test/book/1"},
        {"rel": "http://opds-spec.org/acquisition", "href": "http://opds.test/download.epub", "type": "application/epub+zip"},
        {"rel": "http://opds-spec.org/image", "href": "http://opds.test/cover.jpg"}
    ]
    # support entry.get()
    mock_feed_obj.feed.get = lambda k, d=None: getattr(mock_feed_obj.feed, k, d)
    
    mock_feed.return_value = mock_feed_obj
    monkeypatch.setattr("api.miniapp_routes.get_cached_feed", mock_feed)
    monkeypatch.setenv("DEV_MODE", "True")

    response = client.post("/api/bot", json={
        "action": "book-detail",
        "data": {"bookId": "http://opds.test/book/1"}
    })

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["downloadUrl"] == "http://opds.test/download.epub"
    assert data["cover"] == "http://opds.test/cover.jpg"
