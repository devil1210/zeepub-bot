import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.fixture
def client(monkeypatch):
    # Use patch without autospec to avoid InvalidSpecError if core.bot is already mocked
    with patch("core.bot.ZeePubBot") as mock_bot:
        mock_instance = mock_bot.return_value
        mock_instance.initialize = AsyncMock()
        mock_instance.start_async = AsyncMock()
        mock_instance.stop_async = AsyncMock()

        from api.main import app
        from fastapi.testclient import TestClient

        return TestClient(app)


def test_read_root(client):
    response = client.get("/api_health")
    assert response.status_code == 200


def test_get_feed_no_url(client):
    with patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_parse:
        mock_feed = MagicMock()
        mock_feed.feed.title = "Test Feed"
        entry = MagicMock()
        entry.title = "Book 1"
        entry.author = "Author 1"
        entry.id = "1"
        entry.summary = "Summary"
        entry.links = [
            {
                "href": "http://cover.jpg",
                "rel": "http://opds-spec.org/image",
                "type": "image/jpeg",
            }
        ]
        entry.get = lambda k, d=None: getattr(entry, k, d)

        mock_feed.entries = [entry]
        mock_parse.return_value = mock_feed

        response = client.get("/api/feed?uid=12345")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Feed"


def test_search_books(client):
    with patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_parse:
        mock_feed = MagicMock()
        mock_feed.feed.title = "Search Results"
        mock_feed.entries = []
        mock_parse.return_value = mock_feed

        response = client.get("/api/search?q=harry&uid=12345")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Search Results"
