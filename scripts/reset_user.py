import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add path to find modules
sys.path.append("/app")
sys.path.append(os.getcwd())

from config.config_settings import config
from core.supabase_manager import supabase_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def nuclear_reset_user(telegram_id: int):
    """
    Completely wipes a user from Local DB and Supabase to force clean regeneration.
    """
    load_dotenv()

    db_url = config.DATABASE_URL
    if not db_url:
        logger.error("No DATABASE_URL configured")
        return

    logger.info(f"☢️  INITIATING NUCLEAR RESET FOR USER: {telegram_id} ☢️")

    # 1. Local Postgres Wipe
    try:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            # Delete from dependants first (referential integrity)
            logger.info("Cleaning local tables...")

            # User UI Settings
            await conn.execute(
                text(f"DELETE FROM user_ui_settings WHERE user_id = {telegram_id}")
            )

            # User Ratings / Downloads (Optional - maybe keep history? No, nuclear means nuclear)
            # await conn.execute(text(f"DELETE FROM user_ratings WHERE user_id = {telegram_id}"))
            # await conn.execute(text(f"DELETE FROM user_downloads WHERE user_id = {telegram_id}"))

            # The User record itself
            await conn.execute(
                text(f"DELETE FROM users WHERE telegram_id = {telegram_id}")
            )

            logger.info("✅ Local user record deleted.")

    except Exception as e:
        logger.error(f"❌ Error wiping local DB: {e}")
        return

    # 2. Supabase Wipe
    if config.ENABLE_SUPABASE:
        try:
            logger.info("Cleaning Supabase tables...")
            client = supabase_manager.get_client()

            # UI Settings
            client.table("user_ui_settings").delete().eq(
                "user_id", telegram_id
            ).execute()

            # User
            client.table("users").delete().eq("telegram_id", telegram_id).execute()

            logger.info("✅ Supabase user record deleted.")

        except Exception as e:
            logger.error(f"❌ Error wiping Supabase: {e}")

    logger.info(
        "✨ RESET COMPLETE. Restart the bot and access the Mini App to regenerate."
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to the problematic admin ID
        target_id = 133994080
    else:
        target_id = int(sys.argv[1])

    asyncio.run(nuclear_reset_user(target_id))
