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
