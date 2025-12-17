
import pytest
from unittest.mock import MagicMock, AsyncMock
from telegram import Update, Chat, User, ChatMember, ChatMemberUpdated
from telegram.constants import ChatMemberStatus
from telegram.ext import ContextTypes

# Mock dependencies
import sys
sys.modules["utils.download_limiter"] = MagicMock()
sys.modules["services.user_service"] = MagicMock()
sys.modules["services.opds_service"] = MagicMock()
sys.modules["core.state_manager"] = MagicMock()
sys.modules["config.config_settings"] = MagicMock()

from plugins.custom_messages_plugin import CustomMessagesPlugin

@pytest.mark.asyncio
async def test_welcome_handler_uses_fallback():
    plugin = CustomMessagesPlugin()
    
    # Mock _get_setting to return None (no custom welcome set)
    plugin._get_setting = MagicMock(return_value=None)
    # Mock _get_message to return None (not in DB)
    plugin._get_message = MagicMock(return_value=None)
    
    # Mock context
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    context.bot.copy_message = AsyncMock()
    
    # Mock update: MY_CHAT_MEMBER
    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = -1001
    
    # Simulate adding bot: Left -> Administrator (Channel scenario)
    old_member = MagicMock(spec=ChatMember)
    old_member.status = ChatMemberStatus.LEFT
    
    new_member = MagicMock(spec=ChatMember)
    new_member.status = ChatMemberStatus.ADMINISTRATOR
    
    my_chat_member = MagicMock(spec=ChatMemberUpdated)
    my_chat_member.old_chat_member = old_member
    my_chat_member.new_chat_member = new_member
    
    update.my_chat_member = my_chat_member
    
    # Run handler
    await plugin.welcome_handler(update, context)
    
    # Assert
    # Should have called send_message with default text for "bot_presentation"
    assert context.bot.send_message.called
    args, kwargs = context.bot.send_message.call_args
    assert kwargs['chat_id'] == -1001
    assert "Soy ZeePub Bot" in kwargs['text']
