import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from api.routes import tunnel_opds
from config.config_settings import config


@pytest.mark.asyncio
async def test_tunnel_opds_access():
    # Test Access Control via the dependency directly
    from api.deps import require_mini_app_access

    user_data = {"has_mini_app_access": False, "role": "free"}
    with pytest.raises(HTTPException) as exc:
        await require_mini_app_access(user_data)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_tunnel_opds_streaming():
    # Test functionality
    with patch(
        "api.routes.get_effective_user", new_callable=AsyncMock
    ) as mock_get_user, patch("httpx.AsyncClient") as mock_client_cls:

        mock_get_user.return_value = {"has_mini_app_access": True}

        # Mock Client and Response
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client_cls.return_value = mock_client

        # Use a real Response object if possible, or a mock that behaves like one
        import httpx

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/atom+xml"}
        mock_response.text = "<feed><id>root</id></feed>"

        # Mock aiter_bytes for streaming
        async def byte_iterator():
            yield b"<feed>"
            yield b"</feed>"

        mock_response.aiter_bytes = byte_iterator
        mock_client.get.return_value = mock_response

        response = await tunnel_opds(
            url="http://opds.server/catalog",
            admin_mode=False,
            user_data={"has_mini_app_access": True, "user_id": 1},
        )

        # Verify it returns a Response (it was modified XML)
        from fastapi.responses import Response

        assert isinstance(response, Response)

        # Verify auth was injected
        mock_client.get.assert_called()
        call_kwargs = mock_client.get.call_args.kwargs
        assert "auth" in call_kwargs
        assert call_kwargs["auth"] == config.OPDS_AUTH
