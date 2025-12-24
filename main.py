#!/usr/bin/env python3
import logging
from config.config_settings import config
from core.bot import ZeePubBot

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
)
# Silenciar bibliotecas ruidosas
for logger_name in ["aiosqlite", "httpcore", "httpx", "telegram", "apscheduler"]:
    logging.getLogger(logger_name).setLevel(logging.INFO)
    # También silenciamos sub-loggers
    for sub in ["http11", "connection", "ext"]:
        logging.getLogger(f"{logger_name}.{sub}").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main():
    logger.info("Iniciando ZeePub Bot...")
    is_valid, missing = config.validate()
    if not is_valid:
        logger.error(f"Faltan variables de entorno: {', '.join(missing)}")
        return

    bot = ZeePubBot()
    bot.start()
    logger.info("Bot detenido.")


if __name__ == "__main__":
    main()
