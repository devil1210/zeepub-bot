import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock config
# We need to ensure we don't import real config if it depends on env vars that might fail
# But we usually want real config imports if possible to test real failures.
# However, for a debug script, mocking config is safer to isolate plugin logic.

# In the reported issue, the bot IS running (user says "se murieron"), so environment is likely "fine" but logic is broken.
# Let's try to import without mocking config first, assuming dependencies are present.
# If that fails, we fallback.


async def test_load():
    try:
        print("Importing CustomMessagesPlugin...")
        from plugins.custom_messages_plugin import CustomMessagesPlugin

        plugin = CustomMessagesPlugin()

        # Real config mock

        # config might define enablement for custom messages?

        print("Initializing CustomMessagesPlugin...")
        bot_instance = MagicMock()
        success = await plugin.initialize(bot_instance)
        print(f"Initialization result: {success}")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_load())
