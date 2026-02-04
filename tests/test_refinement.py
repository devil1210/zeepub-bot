from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def client(monkeypatch):
    with patch("core.bot.ZeePubBot") as mock_bot:
        mock_instance = mock_bot.return_value
        mock_instance.initialize = AsyncMock()

        # Ensure routes are registered
        monkeypatch.setenv("ENABLE_MINI_APP", "True")

        import importlib

        import api.main

        importlib.reload(api.main)
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)


@pytest.fixture
def mock_opds_roots(monkeypatch):
    from config.config_settings import config

    monkeypatch.setattr(config, "OPDS_ROOT_START_SUFFIX", "/start")
    monkeypatch.setattr(config, "OPDS_ROOT_EVIL_SUFFIX", "/evil")
    monkeypatch.setattr(config, "OPDS_SERVER_URL", "http://opds.test")
    monkeypatch.setattr(config, "ADMIN_USERS", {123})
    monkeypatch.setattr(config, "VIP_LIST", {456})
    monkeypatch.setattr(config, "PREMIUM_LIST", {789})
    monkeypatch.setattr(config, "WHITELIST", {111})


def test_role_based_access_admin(mock_opds_roots, client):
    with patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed_obj = MagicMock()
        mock_feed_obj.feed.title = "Evil Root"
        mock_feed_obj.entries = []
        mock_feed.return_value = mock_feed_obj

        response = client.get("/api/feed?uid=123")
        assert response.status_code == 200
        assert response.json()["title"] == "Evil Root"


def test_role_based_access_vip(mock_opds_roots, client):
    with patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed_obj = MagicMock()
        mock_feed_obj.feed.title = "Start Root"
        mock_feed_obj.entries = []
        mock_feed.return_value = mock_feed_obj

        response = client.get("/api/feed?uid=456")
        assert response.status_code == 200
        assert response.json()["title"] == "Start Root"


def test_role_based_access_whitelist(mock_opds_roots, client):
    with patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_feed:
        mock_feed_obj = MagicMock()
        mock_feed_obj.feed.title = "Start Root"
        mock_feed_obj.entries = []
        mock_feed.return_value = mock_feed_obj

        response = client.get("/api/feed?uid=111")
        assert response.status_code == 200
        assert response.json()["title"] == "Start Root"


def test_role_based_access_denied(mock_opds_roots, client):
    with patch("api.deps.get_effective_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": False}
        response = client.get("/api/feed?uid=999")
        assert response.status_code == 403


def test_book_detail_parsing(client, monkeypatch):
    with (
        patch("api.miniapp_handlers.get_cached_feed", new_callable=AsyncMock) as mock_feed,
        patch("repositories.metrics_repository.metrics_repo") as mock_metrics,
    ):
        mock_feed_obj = MagicMock()
        mock_feed_obj.entries = []
        mock_feed_obj.feed.title = "Test Book"
        mock_feed_obj.feed.authors = []
        mock_feed_obj.feed.content = []
        mock_feed_obj.feed.links = [
            {"rel": "self", "href": "http://opds.test/book/1"},
            {
                "rel": "http://opds-spec.org/acquisition",
                "href": "http://opds.test/download.epub",
                "type": "application/epub+zip",
            },
            {"rel": "http://opds-spec.org/image", "href": "http://opds.test/cover.jpg"},
        ]
        mock_feed_obj.feed.get = lambda k, d=None: getattr(mock_feed_obj.feed, k, d)
        mock_feed.return_value = mock_feed_obj

        # Mock metrics_repo
        mock_metrics.has_downloaded = AsyncMock(return_value=False)
        mock_metrics.get_total_downloads = AsyncMock(return_value=0)
        mock_metrics.get_rating_stats = AsyncMock(return_value={"average": 0.0, "count": 0})

        monkeypatch.setenv("DEV_MODE", "True")
        from config.config_settings import config

        config.WHITELIST.add(123)

        response = client.post(
            "/api/bot?uid=123",
            json={
                "action": "book-detail",
                "data": {"bookId": "http://opds.test/book/1"},
            },
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Book"
