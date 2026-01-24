from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from plugins.help_plugin import HelpPlugin


@pytest.mark.asyncio
async def test_add_menu_cmd_success():
    plugin = HelpPlugin()
    plugin.enabled = True

    # Mocking admin check
    with patch.object(HelpPlugin, "_is_bot_admin", return_value=True):
        update = MagicMock(spec=Update)
        update.effective_user.id = 123
        update.message = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["search"]
        context.bot = AsyncMock()

        with patch("plugins.help_plugin.get_setting", return_value=""), patch(
            "plugins.help_plugin.set_setting"
        ) as mock_set:

            await plugin.add_menu_cmd(update, context)

            mock_set.assert_called_with("menu_public_commands", "search")
            update.message.reply_text.assert_called()
            # Verify update_bot_commands was called
            assert context.bot.set_my_commands.called or context.bot.method_calls


@pytest.mark.asyncio
async def test_del_menu_cmd_success():
    plugin = HelpPlugin()
    plugin.enabled = True

    with patch.object(HelpPlugin, "_is_bot_admin", return_value=True):
        update = MagicMock(spec=Update)
        update.message = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["search"]
        context.bot = AsyncMock()

        with patch(
            "plugins.help_plugin.get_setting", return_value="start,search"
        ), patch("plugins.help_plugin.set_setting") as mock_set:

            await plugin.del_menu_cmd(update, context)

            mock_set.assert_called_with("menu_public_commands", "start")
            update.message.reply_text.assert_called()


@pytest.mark.asyncio
async def test_list_menu_cmd():
    plugin = HelpPlugin()

    with patch.object(HelpPlugin, "_is_bot_admin", return_value=True):
        update = MagicMock(spec=Update)
        update.message = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

        with patch("plugins.help_plugin.get_setting", return_value="start,help"):
            await plugin.list_menu_cmd(update, context)

            args, kwargs = update.message.reply_text.call_args
            assert "/start" in args[0]
            assert "/help" in args[0]


@pytest.mark.asyncio
async def test_move_menu_cmd_success():
    plugin = HelpPlugin()

    with patch.object(HelpPlugin, "_is_bot_admin", return_value=True):
        update = MagicMock(spec=Update)
        update.message = AsyncMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = ["search", "1"]
        context.bot = AsyncMock()

        with patch(
            "plugins.help_plugin.get_setting", return_value="start,help,search"
        ), patch("plugins.help_plugin.set_setting") as mock_set:

            await plugin.move_menu_cmd(update, context)

            # search should be at index 0 now (pos 1)
            mock_set.assert_called_with("menu_public_commands", "search,start,help")
            update.message.reply_text.assert_called()
