import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from services.publisher.publisher_service import PublisherService
from models.library import LocalBook, SeriesMetadata, TranslatorsGroup, GroupContactLink
from api.handlers.publisher import handle_pub_update_post


@pytest.mark.asyncio
async def test_update_published_book_facebook_success():
    # 1. Setup mock book with fb_post_id
    mock_series = SeriesMetadata(name="Mushoku Tensei", series_spanish="Reencarnación de un Desempleado")
    mock_book = LocalBook(
        id="hash_mushoku_1",
        title="Mushoku Tensei Vol 1",
        volume="1",
        author="Rifujin na Magonote",
        fb_post_id="123456_789012",
        series_info=mock_series,
    )

    mock_group = TranslatorsGroup(name="Mushoku Fansub")
    mock_group.contact_links = [GroupContactLink(platform="website", url="https://mushoku.fans")]

    mock_session = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = mock_book
    mock_session.execute.return_value = mock_exec_res
    service = PublisherService(mock_session)

    service.book_repo = AsyncMock()
    service.book_repo.get_by_hash.return_value = mock_book

    mock_fb_provider = MagicMock()
    mock_fb_provider.update_post_message = AsyncMock(return_value=True)
    service.providers["facebook"] = mock_fb_provider

    with patch("services.workgroup_service.workgroup_service.resolve_book_workgroup_credits",
               return_value={"traductor": "Mushoku Fansub", "traductor_link": "https://mushoku.fans"}):
        res = await service.update_published_book("hash_mushoku_1")
        assert res["success"] is True
        assert res["platforms"]["facebook"] is True
        mock_fb_provider.update_post_message.assert_called_once()
        call_args = mock_fb_provider.update_post_message.call_args[1]
        assert call_args["post_id"] == "123456_789012"
        assert "Mushoku Tensei" in call_args["new_message"]


@pytest.mark.asyncio
async def test_update_published_book_no_fb_post_id():
    mock_book = LocalBook(
        id="hash_solo_leveling_1",
        title="Solo Leveling Vol 1",
        volume="1",
        fb_post_id=None,
        fb_photo_id=None,
    )

    mock_session = AsyncMock()
    mock_exec_res = MagicMock()
    mock_exec_res.scalar_one_or_none.return_value = mock_book
    mock_session.execute.return_value = mock_exec_res
    service = PublisherService(mock_session)
    service.book_repo = AsyncMock()
    service.book_repo.get_by_hash.return_value = mock_book

    with patch("services.workgroup_service.workgroup_service.resolve_book_workgroup_credits", return_value={}):
        res = await service.update_published_book("hash_solo_leveling_1")
        assert res["success"] is False
        assert res["platforms"]["facebook"] is False
        assert "no tiene un post_id" in res["facebook_note"]


@pytest.mark.asyncio
async def test_handle_pub_update_post_handler():
    mock_user = {"user_id": 133994080, "role": "admin", "has_mini_app_access": True}

    with patch("services.publisher.publisher_service.publisher_service.update_published_book",
               return_value={"success": True, "platforms": {"facebook": True}}):
        response = await handle_pub_update_post(
            {"book_id": "test_hash_123", "caption": "Updated caption"},
            mock_user
        )
        assert response["success"] is True
        assert response["result"]["platforms"]["facebook"] is True
