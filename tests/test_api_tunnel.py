import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from api.routes import tunnel_opds
from config.config_settings import config

@pytest.mark.asyncio
async def test_tunnel_opds_access():
    # Test Access Control
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {"has_mini_app_access": False}
        with pytest.raises(HTTPException) as exc:
            await tunnel_opds(url="http://test", current_uid=1)
        assert exc.value.status_code == 403

@pytest.mark.asyncio
async def test_tunnel_opds_streaming():
    # Test functionality
    with patch("api.routes.get_effective_user", new_callable=AsyncMock) as mock_get_user, \
         patch("httpx.AsyncClient") as mock_client_cls:
        
        mock_get_user.return_value = {"has_mini_app_access": True}
        
        # Mock Client and Response
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/atom+xml"}
        
        # Mock aiter_bytes for streaming
        async def byte_iterator():
            yield b"<feed>"
            yield b"</feed>"
        
        mock_response.aiter_bytes = byte_iterator
        mock_client.send.return_value = mock_response
        
        response = await tunnel_opds(url="http://opds.server/catalog", current_uid=1)
        
        # Verify it returns a StreamingResponse
        from fastapi.responses import StreamingResponse
        assert isinstance(response, StreamingResponse)
        
        # Verify auth was injected
        mock_client.build_request.assert_called()
        call_kwargs = mock_client.build_request.call_args.kwargs
        assert "auth" in call_kwargs
        assert call_kwargs["auth"] == config.OPDS_AUTH
