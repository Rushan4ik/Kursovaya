from bot import create_bot
from config import settings
from db.session import init_db
from utils.logging_config import setup_logging
import logging


def main() -> None:
    setup_logging(settings.log_file)
    init_db()
    bot = create_bot()
    logging.info("FakeNewsBot запущен")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)


if __name__ == "__main__":
    main()
