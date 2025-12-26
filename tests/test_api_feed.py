import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from api.routes import get_feed
from config.config_settings import config

# Mock entry with links
class MockEntry:
    def __init__(self, title, links=None, id="1"):
        self.title = title
        self.links = links or []
        self.id = id
        self.summary = "Summary"
        self.content = []  # Added for cover check compatibility
        
    def get(self, key, default=None):
        if key == "title": return self.title
        if key == "links": return self.links
        if key == "id": return self.id
        if key == "summary": return self.summary
        return default

class MockFeed:
    def __init__(self, entries):
        self.entries = entries
        self.feed = MagicMock()
        self.feed.get.return_value = None # default for optional fields

@pytest.mark.asyncio
async def test_get_feed_access_control():
    # Test 1: User with has_mini_app_access=False should raise 403
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": False}
        
        with pytest.raises(HTTPException) as excinfo:
            await get_feed(url=None, current_uid=123)
        assert excinfo.value.status_code == 403

    # Test 2: User with has_mini_app_access=True should pass
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed:
        
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": True}
        mock_get_feed.return_value = MockFeed([]) # Return empty feed
        
        # Should not raise exception
        await get_feed(url="http://test.com", current_uid=123)

@pytest.mark.asyncio
async def test_get_feed_renaming_logic():
    # Test "Todas las bibliotecas" renaming for non-admin
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed, \
         patch("api.routes.find_zeepubs_destino") as mock_find_zeepubs:
        
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": True}
        
        # Setup mock feed with "Todas las bibliotecas"
        entries = [
            MockEntry("Todas las bibliotecas", links=[{"rel": "subsection", "href": "http://libs"}])
        ]
        mock_get_feed.side_effect = [
            MockFeed(entries),          # First call (main feed)
            MockFeed([])                # Second call (fetching subsection to find zeepubs)
        ]
        
        mock_find_zeepubs.return_value = "http://direct-zeepubs-es"
        
        result = await get_feed(url="http://root", current_uid=123)
        
        # Verify renaming
        assert result["entries"][0]["title"] == "Biblioteca Zeepubs"
        # Verify link override
        assert result["entries"][0]["subsection_url"] == "http://direct-zeepubs-es"

@pytest.mark.asyncio
async def test_get_feed_no_renaming_for_admin():
    # Test NO renaming for admin
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed:
        
        mock_get_user.return_value = {"role": "admin", "has_mini_app_access": True}
        
        entries = [
            MockEntry("Todas las bibliotecas", links=[{"rel": "subsection", "href": "http://libs"}])
        ]
        mock_get_feed.return_value = MockFeed(entries)
        
        result = await get_feed(url="http://root", current_uid=999)
        
        # Verify NO renaming
        assert result["entries"][0]["title"] == "Todas las bibliotecas"

@pytest.mark.asyncio
async def test_get_feed_evil_url_protection():
    # Test that non-admin requesting Evil URL gets content from Start URL (or redirected logic)
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed, \
         patch("config.config_settings.config.OPDS_SERVER_URL", "http://root"), \
         patch("config.config_settings.config.OPDS_ROOT_EVIL_SUFFIX", "/evil"), \
         patch("config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"):
        
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": True}
        
        # Determine behavior: logic calls get_cached_feed with the TARGET url.
        # We expect TARGET to be switched to START because we passed an evil-ish URL
        mock_get_feed.return_value = MockFeed([])
        
        await get_feed(url="http://root/evil/secret", current_uid=123)
        
        # Verify get_cached_feed was called with START url, not EVIL url
        # Logic: target_url = config.OPDS_ROOT_START
        # Note: mocking config attributes usually requires patching the object where it is used or the class.
        # Here we patch the property or attribute on the imported config object.
        # We need to verify what mock_get_feed was called with.
        
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/start"

@pytest.mark.asyncio
async def test_get_feed_admin_default_start():
    # Test that Admin defaults to Start URL if no URL provided (Admin Mode Switch dependent)
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed, \
         patch("config.config_settings.config.OPDS_SERVER_URL", "http://root"), \
         patch("config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"):
        
        mock_get_user.return_value = {"role": "admin", "has_mini_app_access": True}
        mock_get_feed.return_value = MockFeed([])
        
        # Calling without URL should default to START, not EVIL
        await get_feed(url=None, current_uid=1)
        
        # Verify it fetched START
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/start" 

@pytest.mark.asyncio
async def test_get_feed_staff_evil_access():
    # Test that Staff CAN access Evil URL explicitly
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed, \
         patch("config.config_settings.config.OPDS_SERVER_URL", "http://root"), \
         patch("config.config_settings.config.OPDS_ROOT_EVIL_SUFFIX", "/evil"):
         
        mock_get_user.return_value = {"role": "staff", "has_mini_app_access": True}
        mock_get_feed.return_value = MockFeed([])
        
        await get_feed(url="http://root/evil", current_uid=2)
        
        # Verify it ALLOWED evil url
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/evil"

@pytest.mark.asyncio
async def test_tunnel_opds_slash_url_defaults():
    # Test that /api/tunnel/opds?url=/ triggers default Start Catalog
    from api.routes import tunnel_opds
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.httpx.AsyncClient") as mock_client_class, \
         patch("config.config_settings.config.OPDS_SERVER_URL", "http://root"), \
         patch("config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"):
        
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": True}
        
        # Mock httpx client
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/atom+xml"}
        mock_response.aiter_bytes.return_value = [] # Async iterator
        
        mock_client.send.return_value = mock_response
        
        # Calling with url="/"
        await tunnel_opds(url="/", current_uid=123)
        
        # Should build request with FULL Start URL
        args, _ = mock_client.build_request.call_args
        assert args[1] == "http://root/start"

@pytest.mark.asyncio
async def test_get_feed_slash_url_defaults():
    # Test that url="/" triggers default Start Catalog
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("api.routes.get_cached_feed", new_callable=AsyncMock) as mock_get_feed, \
         patch("config.config_settings.config.OPDS_SERVER_URL", "http://root"), \
         patch("config.config_settings.config.OPDS_ROOT_START_SUFFIX", "/start"):
        
        mock_get_user.return_value = {"role": "free", "has_mini_app_access": True}
        mock_get_feed.return_value = MockFeed([])
        
        # Calling with url="/"
        await get_feed(url="/", current_uid=123)
        
        # Should call with FULL Start URL
        args, _ = mock_get_feed.call_args
        assert args[0] == "http://root/start"
