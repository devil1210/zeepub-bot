from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from services.publisher.publisher_service import FacebookPublisherProvider


def make_mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = str(json_data)
    resp.json = MagicMock(return_value=json_data or {})
    return resp


@pytest.mark.asyncio
async def test_facebook_resolve_credentials():
    provider = FacebookPublisherProvider()
    mock_resp = make_mock_response(
        200,
        {
            "data": [
                {"id": "123456", "access_token": "PAGE_ACCESS_TOKEN_XYZ"}
            ]
        }
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp):
        page_id, token = await provider._resolve_credentials("123456", "USER_TOKEN_123")
        assert page_id == "123456"
        assert token == "PAGE_ACCESS_TOKEN_XYZ"


@pytest.mark.asyncio
async def test_facebook_get_or_create_series_album_finds_existing():
    provider = FacebookPublisherProvider()
    mock_resp = make_mock_response(
        200,
        {
            "data": [
                {"id": "album_999", "name": "Mushoku Tensei"}
            ]
        }
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_resp), \
         patch.object(provider, "_persist_series_album_id", new_callable=AsyncMock):
        album_id = await provider.get_or_create_series_album(
            target_page_id="123456",
            token="TOKEN",
            series_name="Mushoku Tensei",
            series_id="series_hash_1",
        )
        assert album_id == "album_999"


@pytest.mark.asyncio
async def test_facebook_get_or_create_series_album_creates_new():
    provider = FacebookPublisherProvider()
    mock_get_resp = make_mock_response(200, {"data": []})
    mock_post_resp = make_mock_response(201, {"id": "album_new_777"})

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_get_resp), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_post_resp), \
         patch.object(provider, "_persist_series_album_id", new_callable=AsyncMock):
        album_id = await provider.get_or_create_series_album(
            target_page_id="123456",
            token="TOKEN",
            series_name="Overlord",
            series_id="series_hash_2",
        )
        assert album_id == "album_new_777"


@pytest.mark.asyncio
async def test_facebook_publish_photo_to_album():
    provider = FacebookPublisherProvider()
    mock_post_resp = make_mock_response(
        200,
        {
            "id": "photo_123",
            "post_id": "post_story_456"
        }
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_post_resp):
        res = await provider.publish_photo_to_album(
            album_id="album_999",
            resolved_cover=b"fake_image_bytes",
            cover_source=None,
            caption="Test Caption",
            token="PAGE_TOKEN",
        )
        assert res is not None
        assert res["photo_id"] == "photo_123"
        assert res["post_id"] == "post_story_456"


@pytest.mark.asyncio
async def test_facebook_update_post_message():
    provider = FacebookPublisherProvider()
    mock_post_resp = make_mock_response(200, {"success": True})

    with patch.object(provider, "_resolve_credentials", return_value=("page_123", "token_123")), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_post_resp):
        success = await provider.update_post_message(
            post_id="post_story_456",
            new_message="Updated Caption Text",
            token="token_123",
        )
        assert success is True


@pytest.mark.asyncio
async def test_facebook_announce_book_album_flow():
    provider = FacebookPublisherProvider()

    book_data = {
        "id": "book_hash_1",
        "book_hash": "book_hash_1",
        "title": "Volumen 1",
        "series_spanish": "Mushoku Tensei",
        "series_id": "series_hash_1",
        "cover_original": "http://example.com/cover.jpg",
    }

    with patch.object(provider, "_resolve_credentials", return_value=("page_123", "token_123")), \
         patch.object(provider, "get_or_create_series_album", return_value="album_999"), \
         patch.object(provider, "publish_photo_to_album", return_value={"photo_id": "p1", "post_id": "post_1"}), \
         patch.object(provider, "_persist_book_fb_ids", new_callable=AsyncMock), \
         patch("utils.helpers.validate_facebook_credentials", return_value=(True, "")):
        success = await provider.announce_book("page_123", book_data)
        assert success is True
