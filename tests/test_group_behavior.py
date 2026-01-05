import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Patch dependencies in sys.modules ONLY for the duration of the test."""
    modules_to_patch = {
        "core": MagicMock(),
        "core.bot": MagicMock(),
        "core.state_manager": MagicMock(),
        "core.session_manager": MagicMock(),
        "handlers.command_handlers": MagicMock(),
        "handlers.callback_handlers": MagicMock(),
        "services": MagicMock(),
        "services.opds_service": MagicMock(),
        "services.user_service": MagicMock(),
        "utils": MagicMock(),
        "utils.http_client": MagicMock(),
        "utils.helpers": MagicMock(),
        "config": MagicMock(),
    }
    modules_to_patch["services.user_service"].get_effective_user = AsyncMock(return_value={"role": "free"})

    with patch.dict(sys.modules, modules_to_patch):
        # We need to ensure handlers.message_handlers is reloaded if already imported
        if "handlers.message_handlers" in sys.modules:
            import importlib
            importlib.reload(sys.modules["handlers.message_handlers"])
        yield

@pytest.mark.asyncio
async def test_recibir_texto_group_chat_suppression(monkeypatch):
    from handlers.message_handlers import recibir_texto
    update = MagicMock()
    context = MagicMock()
    update.effective_user.id = 123
    update.effective_chat.id = 456
    update.effective_chat.type = 'group'
    update.message.text = "some random text"

    mock_state_manager = MagicMock()
    mock_state_manager.get_user_state.return_value = {}

    # Use a local reference to state_manager in the module
    import handlers.message_handlers as mh
    monkeypatch.setattr(mh, "state_manager", mock_state_manager)

    mock_config = MagicMock()
    mock_config.get_six_hour_password.return_value = "password"
    monkeypatch.setattr(mh, "config", mock_config)

    context.bot.send_message = AsyncMock()
    await recibir_texto(update, context)
    context.bot.send_message.assert_not_called()

@pytest.mark.asyncio
async def test_recibir_texto_group_chat_with_active_state(monkeypatch):
    from handlers.message_handlers import recibir_texto
    import handlers.message_handlers as mh
    update = MagicMock()
    context = MagicMock()
    update.effective_user.id = 123
    update.effective_chat.id = 456
    update.effective_chat.type = 'group'
    update.message.text = "password"

    mock_state_manager = MagicMock()
    mock_state_manager.get_user_state.return_value = {"esperando_password": True}
    monkeypatch.setattr(mh, "state_manager", mock_state_manager)

    mock_config = MagicMock()
    mock_config.get_six_hour_password.return_value = "password"
    monkeypatch.setattr(mh, "config", mock_config)

    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    await recibir_texto(update, context)
    context.bot.send_message.assert_called()

@pytest.mark.asyncio
async def test_recibir_texto_private_chat_response(monkeypatch):
    from handlers.message_handlers import recibir_texto
    import handlers.message_handlers as mh
    update = MagicMock()
    context = MagicMock()
    update.effective_user.id = 123
    update.effective_chat.id = 456
    update.effective_chat.type = 'private'
    update.message.text = "some random text"

    mock_state_manager = MagicMock()
    mock_state_manager.get_user_state.return_value = {}
    monkeypatch.setattr(mh, "state_manager", mock_state_manager)

    mock_config = MagicMock()
    mock_config.get_six_hour_password.return_value = "password"
    monkeypatch.setattr(mh, "config", mock_config)

    context.bot.send_message = AsyncMock()
    mock_cms = MagicMock()
    mock_cms.enabled = True
    mock_cms.get_text = AsyncMock(return_value="Usa /start para comenzar")
    context.application.plugin_manager.get_plugin.return_value = mock_cms

    await recibir_texto(update, context)
    context.bot.send_message.assert_called_once()
    args, kwargs = context.bot.send_message.call_args
    assert "Usa /start para comenzar" in kwargs.get('text', '')
