import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from api.routes import get_feed, tunnel_opds
from api.deps import require_mini_app_access


# Mock entry with links
class MockEntry:
    def __init__(self, title, links=None, id="1"):
        self.title = title
        self.links = links or []
        self.id = id
        self.summary = "Summary"
        self.content = []  # Added for cover check compatibility

    def get(self, key, default=None):
        if key == "title":
            return self.title
        if key == "links":
            return self.links
        if key == "id":
            return self.id
        if key == "summary":
            return self.summary
        return default


class MockFeed:
    def __init__(self, entries):
        self.entries = entries
        self.feed = MagicMock()
        self.feed.get.return_value = None  # default for optional fields


@pytest.mark.asyncio
async def test_get_feed_access_control():
    # Test 1: User with has_mini_app_access=False should raise 403
    user_data = {"role": "free", "has_mini_app_access": False}
    with pytest.raises(HTTPException) as excinfo:
        await require_mini_app_access(user_data)
    assert excinfo.value.status_code == 403

    # Test 2: Admin should pass regardless of has_mini_app_access
    admin_data = {"role": "admin", "has_mini_app_access": False}
    result = await require_mini_app_access(admin_data)
    assert result == admin_data

    # Test 3: User with has_mini_app_access=True should pass
    valid_data = {"role": "free", "has_mini_app_access": True}
    result = await require_mini_app_access(valid_data)
    assert result == valid_data


@pytest.mark.asyncio
async def test_get_feed_renaming_logic():
    # Test "Todas las bibliotecas" renaming for non-admin
    with patch(
        "api.routes.get_cached_feed", new_callable=AsyncMock
    ) as mock_get_feed, patch(
        "api.routes.find_zeepubs_destino"
    ) as mock_find_zeepubs:


        # Setup mock feed with "Todas las bibliotecas"
        entries = [
            MockEntry(
                "Todas las bibliotecas",
                links=[{"rel": "subsection", "href": "http://libs"}],
            )
        ]
        mock_get_feed.side_effect = [
            MockFeed(entries),  # 1. First call (main feed)
            MockFeed(
                [
                    MockEntry(
                        "ZeePubs ES",
                        links=[
                            {"rel": "subsection", "href": "http://direct-zeepubs-es"}
                        ],
                    )
                ]
            ),  # 2. libraries listing
            MockFeed(
                [
                    MockEntry(
                        "First Lib",
                        links=[{"rel": "subsection", "href": "http://final-deep-link"}],
                    )
                ]
            ),  # 3. ZeePubs ES listing
        ]

        mock_find_zeepubs.return_value = "http://direct-zeepubs-es"

        result = await get_feed(
            url="http://root", user_data={"role": "free", "has_mini_app_access": True}
        )

        # Verify renaming
        assert result["entries"][0]["title"] == "Mi Catálogo"
        # Verify link override
        assert result["entries"][0]["subsection_url"] == "http://final-deep-link"


@pytest.mark.asyncio
async def test_get_feed_no_renaming_for_admin():
    # Test NO renaming for admin
    with patch(
        "api.routes.get_cached_feed", new_callable=AsyncMock
    ) as mock_get_feed:


        entries = [
            MockEntry(
                "Todas las bibliotecas",
                links=[{"rel": "subsection", "href": "http://libs"}],
            )
        ]
        mock_get_feed.return_value = MockFeed(entries)

        result = await get_feed(
            url="http://root", user_data={"role": "admin", "has_mini_app_access": True}
        )

        # Verify Unified renaming (now everyone sees Mi Catálogo)
        assert result["entries"][0]["title"] == "Mi Catálogo"


@pytest.mark.asyncio
async def test_get_feed_evil_url_protection():
    # Test that non-admin requesting Evil URL gets content from Start URL (or redirected logic)
    with patch(
        "api.routes.get_cached_feed", new_callable=AsyncMock
    ) as mock_get_feed, patch(
        "config.config_settings.config.OPDS_SERVER_URL", "http://root"
    ), patch(
        "config.config_settings.config.OPDS_ROOT_EVIL_SUFFIX", "/evil"
    ), patch(
        "config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"
    ):


        # Determine behavior: logic calls get_cached_feed with the TARGET url.
        # We expect TARGET to be switched to START because we passed an evil-ish URL
        mock_get_feed.return_value = MockFeed([])

        await get_feed(
            url="http://root/evil/secret",
            user_data={"role": "free", "has_mini_app_access": True},
        )

        # Verify get_cached_feed was called with START url, not EVIL url
        # Logic: target_url = config.OPDS_ROOT_START
        # Note: mocking config attributes usually requires patching the object where it is used or the class.
        # Here we patch the property or attribute on the imported config object.
        # We need to verify what mock_get_feed was called with.

        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/start"


@pytest.mark.asyncio
async def test_get_feed_admin_default_start(monkeypatch):
    # Test that Admin defaults to Start URL if no URL provided (Admin Mode Switch dependent)
    with patch(
        "api.routes.get_cached_feed", new_callable=AsyncMock
    ) as mock_get_feed:

        from api.routes import config

        monkeypatch.setattr(config, "OPDS_SERVER_URL", "http://root")
        monkeypatch.setattr(config, "OPDS_ROOT_START_SUFFIX", "/start")

        mock_get_feed.return_value = MockFeed([])

        # Calling without URL should default to START, not EVIL
        await get_feed(
            url=None, user_data={"role": "admin", "has_mini_app_access": True}
        )

        # Verify it fetched START
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/start"


@pytest.mark.asyncio
async def test_get_feed_staff_evil_access():
    # Test that Staff CAN access Evil URL explicitly
    with patch(
        "api.routes.get_cached_feed", new_callable=AsyncMock
    ) as mock_get_feed, patch(
        "config.config_settings.config.OPDS_SERVER_URL", "http://root"
    ), patch(
        "config.config_settings.config.OPDS_ROOT_EVIL_SUFFIX", "/evil"
    ):

        await get_feed(
            url="http://root/evil",
            user_data={"role": "staff", "has_mini_app_access": True},
        )

        # Verify it ALLOWED evil url
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/evil"


@pytest.mark.asyncio
async def test_tunnel_opds_slash_url_defaults():
    # Test that /api/tunnel/opds?url=/ triggers default Start Catalog

    with patch(
        "api.routes.httpx.AsyncClient"
    ) as mock_client_class, patch(
        "config.config_settings.config.OPDS_SERVER_URL", "http://root"
    ), patch(
        "config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"
    ):


        # Mock httpx client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client

        # Use a simple mock with explicit status_code
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/atom+xml"}
        mock_response.text = "<feed><title>Kavita</title></feed>"

        # For StreamingResponse
        async def mock_iter():
            yield b"<feed><title>Kavita</title></feed>"

        mock_response.aiter_bytes.return_value = mock_iter()

        mock_client.get.return_value = mock_response

        # Calling with url="/"
        await tunnel_opds(
            url="/",
            admin_mode=False,
            user_data={"role": "free", "has_mini_app_access": True},
        )

        # Should call get with FULL Start URL
        args, kwargs = mock_client.get.call_args
        assert args[0] == "http://root/start"


@pytest.mark.asyncio
async def test_get_feed_slash_url_defaults():
    # Test that url="/" triggers default Start Catalog
    with patch(
        "api.routes.get_cached_feed", new_callable=AsyncMock
    ) as mock_get_feed, patch(
        "config.config_settings.config.OPDS_SERVER_URL", "http://root"
    ), patch(
        "config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"
    ):

        mock_get_feed.return_value = MockFeed([])

        # Calling with url="/"
        await get_feed(url="/", user_data={"role": "free", "has_mini_app_access": True})

        # Should call with FULL Start URL
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/start"
