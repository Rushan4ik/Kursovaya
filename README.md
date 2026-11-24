# FakeNewsBot — «Фейк или Правда»

Telegram-бот для учебной игры по распознаванию недостоверных новостей. Реализован на Python, pyTelegramBotAPI, SQLAlchemy 2.x и SQLite.

> В `data/news.csv` находятся только демонстрационные вымышленные записи. Перед полноценной эксплуатацией замените их проверенными новостями из выбранного датасета, добавьте пояснения и источники. Метка в игре берётся из CSV/БД; бот сам не проверяет факты.

## Возможности

- регистрация пользователей через `/start`;
- игровой раунд с кнопками «Фейк» и «Правда»;
- пояснение и ссылка на источник после ответа;
- защита от повторного callback;
- статистика пользователя: раунды, правильные ответы, точность, текущая и максимальная серии;
- сброс просмотренных новостей без удаления журнала ответов;
- администрирование: добавление новостей и сводная статистика;
- загрузка новостей из CSV;
- логирование и тесты.

## Требования

- Python 3.10 или новее;
- Telegram Bot Token от BotFather.

## Установка и локальный запуск

1. Склонируйте репозиторий или распакуйте архив.
2. Создайте виртуальное окружение:

   ```bash
   python -m venv .venv
   ```

   Windows:

   ```bash
   .venv\Scripts\activate
   ```

   Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Скопируйте `.env.example` в `.env` и заполните настройки:

   ```env
   BOT_TOKEN=токен_от_BotFather
   ADMIN_IDS=ваш_telegram_id
   DATABASE_URL=sqlite:///fake_news_bot.db
   LOG_FILE=bot.log
   ```

   Несколько администраторов указываются через запятую.

5. Инициализируйте БД и загрузите демонстрационные записи:

   ```bash
   python -m scripts.init_db
   python -m scripts.load_dataset data/news.csv
   ```

6. Запустите бота:

   ```bash
   python run.py
   ```

## Команды

| Команда | Назначение |
|---|---|
| `/start` | Регистрация и главное меню |
| `/play` | Начать раунд |
| `/stats` | Статистика пользователя |
| `/reset_progress` | Сброс просмотренных новостей |
| `/help` | Список команд |
| `/admin` | Панель администратора |
| `/add_news` | Добавить новость (только администратор) |
| `/news_stats` | Статистика пула (доступна через меню администратора) |

## Формат CSV

Файл должен быть в UTF-8 и содержать заголовки:

```csv
text,is_fake,explanation,source_url,category
"Текст новости длиной от 20 до 1000 символов",true,"Пояснение от 10 до 500 символов","https://example.org","наука"
```

- `is_fake`: `true` — фейк, `false` — правда;
- `source_url` и `category` необязательны;
- повторная загрузка того же CSV добавит записи повторно.

Загрузка:

```bash
python -m scripts.load_dataset data/news.csv
```

Для соответствия ТЗ подготовьте не менее 100 проверенных записей; доля фейков должна составлять 40–60%.

## Структура проекта

```text
fake_news_bot/
├── bot.py
├── config.py
├── run.py
├── keyboards.py
├── requirements.txt
├── .env.example
├── README.md
├── db/
│   ├── models.py
│   ├── repository.py
│   └── session.py
├── services/
│   ├── game.py
│   └── stats.py
├── scripts/
│   ├── init_db.py
│   └── load_dataset.py
├── data/
│   └── news.csv
├── tests/
│   ├── conftest.py
│   └── test_game.py
└── utils/
    └── logging_config.py
```

## Тестирование

```bash
pytest -v
```

Тесты проверяют правильный и неправильный ответ, обновление серии, защиту от повторного callback и сохранение журнала ответов после сброса прогресса.

## Развёртывание на VPS (Ubuntu)

1. Установите Python 3.10+ и `venv`.
2. Скопируйте проект на сервер.
3. Выполните установку зависимостей и настройку `.env` по инструкции выше.
4. Проверьте запуск командой `python run.py`.
5. Для постоянной работы создайте systemd unit `/etc/systemd/system/fake-news-bot.service`:

   ```ini
   [Unit]
   Description=FakeNewsBot Telegram bot
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/opt/fake_news_bot
   ExecStart=/opt/fake_news_bot/.venv/bin/python run.py
   Restart=always
   RestartSec=5
   User=ubuntu

   [Install]
   WantedBy=multi-user.target
   ```

6. Включите службу:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now fake-news-bot
   sudo systemctl status fake-news-bot
   ```

Логи приложения пишутся в `bot.log`, системные сообщения доступны через `journalctl -u fake-news-bot -f`.

## Примечания по архитектуре

- `handlers` и отдельные файлы обработчиков можно выделить дополнительно при расширении проекта; в этой учебной версии маршрутизация собрана в `bot.py`.
- `db/repository.py` изолирует доступ к данным от игровой логики.
- SQLite используется по умолчанию. Для PostgreSQL достаточно установить драйвер `psycopg` и задать соответствующий `DATABASE_URL`; миграции схемы при этом следует вести отдельно.
- Polling выбран для локальной разработки и допустим ТЗ для продакшена при обосновании.
