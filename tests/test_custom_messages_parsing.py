import pytest
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from telegram import Update, Message, User
from telegram.ext import ContextTypes

# Do not import the plugin here globally if it depends on patched modules
# from plugins.custom_messages_plugin import CustomMessagesPlugin

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Patch dependencies in sys.modules for the duration of the test."""
    modules_to_patch = {
        "utils.download_limiter": MagicMock(),
        "services.user_service": MagicMock(),
        "services.opds_service": MagicMock(),
        "core.state_manager": MagicMock(),
        "config.config_settings": MagicMock(),
    }
    with patch.dict(sys.modules, modules_to_patch):
        yield

@pytest.mark.asyncio
async def test_saludo_parsing(monkeypatch):
    # Import inside the test after mock_dependencies fixture has run
    from plugins.custom_messages_plugin import CustomMessagesPlugin
    import plugins.custom_messages_plugin as plugin_mod

    # Create a mock config with proper ADMIN_USERS
    mock_config = MagicMock()
    mock_config.ADMIN_USERS = [123]

    # Inject it into the plugin module's namespace
    monkeypatch.setattr(plugin_mod, 'config', mock_config)

    plugin = CustomMessagesPlugin()

    # Mock update and context
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.copy_message = AsyncMock()

    # Mock DB methods to avoid Session error
    plugin._get_message = MagicMock(return_value=None)

    # Test Case 1: Legacy format (no thread ID)
    # /saludo -100123 Hola Mundo
    context.args = ["-100123", "Hola", "Mundo"]

    await plugin.saludo(update, context)

    # Verify text sent to chat -100123, NO thread_id
    context.bot.send_message.assert_called_with(
        chat_id="-100123", text="Hola Mundo", message_thread_id=None
    )

    # Test Case 2: New format (with thread ID)
    # /saludo -100123 445 Hola Mundo
    context.bot.send_message.reset_mock()
    context.args = ["-100123", "445", "Hola", "Mundo"]

    await plugin.saludo(update, context)

    # Verify text sent with thread_id
    context.bot.send_message.assert_called_with(
        chat_id="-100123",
        text="Hola Mundo",
        message_thread_id=445,
    )

    # Let's check call args more loosely if needed or fix expectations
    # The code: await context.bot.send_message(chat_id=target_chat_id, text=content, message_thread_id=message_thread_id)
    # Indeed no parse_mode for raw text.

    call_args = context.bot.send_message.call_args
    assert call_args.kwargs["chat_id"] == "-100123"
    assert call_args.kwargs["text"] == "Hola Mundo"
    assert call_args.kwargs["message_thread_id"] == 445

    # Test Case 3: Slug with Thread ID
    # /saludo -100123 999 existing_slug
    # We need to mock _get_message to return something or TEMPLATE_REGISTRY
    plugin._get_message = MagicMock(return_value=None)

    # Mock get_text
    plugin.get_text = AsyncMock(return_value="Contenido del Template")

    # Fake is_template = True by patching TEMPLATE_REGISTRY
    # Since we imported custom_messages_plugin, we patch it there
    import plugins.custom_messages_plugin as cmp

    # We need to be careful, cmp.TEMPLATE_REGISTRY might need to be patched directly
    # or we rely on logic.
    # But we can just set the dict item since it is mutable
    cmp.TEMPLATE_REGISTRY["existing_slug"] = {"default": "foo"}

    context.bot.send_message.reset_mock()
    context.args = ["-100123", "999", "existing_slug"]

    await plugin.saludo(update, context)

    # verify send_message called with template text and thread_id
    context.bot.send_message.assert_called_with(
        chat_id="-100123",
        text="Contenido del Template",
        parse_mode="HTML",
        message_thread_id=999,
    )

    # Test Case 4: Ambiguous Thread ID (slug is number-like but intended as slug?)
    # /saludo -100123 1234
    # If 1234 IS a slug, and we treat it as thread_id, we fail to find content.
    # But our logic says: if parsable as int > 0, treat as thread_id.
    # Then content is rest. If rest is empty -> Error.

    context.bot.send_message.reset_mock()
    context.args = ["-100123", "1234"]
    update.message.reply_text.reset_mock()

    # This should fail as "Missing content" because 1234 is consumed as thread_id
    await plugin.saludo(update, context)

    update.message.reply_text.assert_called_with("❌ Falta el contenido del mensaje.")
