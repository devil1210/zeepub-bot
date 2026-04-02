from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

import plugins.custom_messages_plugin as plugin_mod
from plugins.custom_messages_plugin import CustomMessagesPlugin


@pytest.mark.asyncio
async def test_welcome_handler_uses_fallback(monkeypatch):
    mock_config = MagicMock()
    monkeypatch.setattr(plugin_mod, "config", mock_config)

    plugin = CustomMessagesPlugin()
    plugin._get_setting = MagicMock(return_value=None)
    plugin._get_message = MagicMock(return_value=None)

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.copy_message = AsyncMock()

    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = -1001

    old_member = MagicMock(spec=ChatMember)
    old_member.status = ChatMemberStatus.LEFT
    new_member = MagicMock(spec=ChatMember)
    new_member.status = ChatMemberStatus.ADMINISTRATOR

    my_chat_member = MagicMock(spec=ChatMemberUpdated)
    my_chat_member.old_chat_member = old_member
    my_chat_member.new_chat_member = new_member
    update.my_chat_member = my_chat_member

    await plugin.welcome_handler(update, context)
    assert context.bot.send_message.called
    args, kwargs = context.bot.send_message.call_args
    assert kwargs["chat_id"] == -1001
    assert "Soy ZeePub Bot" in kwargs["text"]
