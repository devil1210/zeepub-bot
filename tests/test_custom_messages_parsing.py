from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Message, Update, User
from telegram.ext import ContextTypes

import plugins.custom_messages_plugin as plugin_mod
from plugins.custom_messages_plugin import CustomMessagesPlugin


@pytest.mark.asyncio
async def test_saludo_parsing(monkeypatch):
    mock_config = MagicMock()
    mock_config.ADMIN_USERS = [123]
    monkeypatch.setattr(plugin_mod, "config", mock_config)

    plugin = CustomMessagesPlugin()
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()

    plugin._get_message = MagicMock(return_value=None)
    context.args = ["-100123", "Hola", "Mundo"]

    await plugin.saludo(update, context)
    context.bot.send_message.assert_called_with(chat_id="-100123", text="Hola Mundo", message_thread_id=None)
