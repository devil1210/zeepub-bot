import asyncio
from telegram import Bot
from config.config_settings import config

async def test():
    bot = Bot(token=config.TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id='-1001629767492', text="Test message string channel id")
        print("Success for -1001629767492!")
    except Exception as e:
        print(f"Error for -1001629767492: {str(e)}")
        
    try:
        await bot.send_message(chat_id=133994080, text="Test message int chat id")
        print("Success for 133994080!")
    except Exception as e:
        print(f"Error for 133994080: {str(e)}")

asyncio.run(test())
