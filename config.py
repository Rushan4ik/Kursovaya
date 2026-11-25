import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: set[int]
    database_url: str
    log_file: str


def _parse_admin_ids(value: str) -> set[int]:
    result = set()
    for item in value.split(","):
        item = item.strip()
        if item:
            try:
                result.add(int(item))
            except ValueError as exc:
                raise ValueError(f"Некорректный ADMIN_IDS: {item}") from exc
    return result


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
    database_url=os.getenv("DATABASE_URL", "sqlite:///fake_news_bot.db"),
    log_file=os.getenv("LOG_FILE", "bot.log"),
)

if not settings.bot_token:
    # Позволяет импортировать модули и запускать тесты без токена.
    pass
