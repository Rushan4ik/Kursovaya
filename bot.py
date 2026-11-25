import logging
from html import escape
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from db.session import get_session
from db import repository
from services.game import start_round, submit_answer
from keyboards import main_menu, game_keyboard, next_keyboard, confirm_reset_keyboard

logger = logging.getLogger(__name__)
ADMIN_STATES = {}  # user_id -> {"step": ..., "data": ...}


def create_bot():
    if not settings.bot_token:
        raise RuntimeError("Не задан BOT_TOKEN. Создайте .env на основе .env.example.")
    bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML")

    def send_rules(chat_id):
        bot.send_message(
            chat_id,
            "<b>Правила игры</b>\nПрочитайте новость и выберите, считаете ли вы её фейком "
            "или правдой. После ответа вы увидите разбор. Метка определяется учебным "
            "датасетом, бот не является профессиональным фактчекером.",
            reply_markup=main_menu()
        )

    def send_round(chat_id, user_id):
        session = get_session()
        try:
            result = start_round(session, user_id)
            if result is None:
                bot.send_message(
                    chat_id,
                    "Вы просмотрели все доступные новости. Чтобы пройти их заново, "
                    "используйте /reset_progress.",
                    reply_markup=main_menu()
                )
                return
            news, token = result
            text = news.text
            bot.send_message(
                chat_id,
                f"<b>Новость #{news.id}</b>\n\n{escape(text)}",
                reply_markup=game_keyboard(news.id, token)
            )
        finally:
            session.close()

    @bot.message_handler(commands=["start"])
    def start(message):
        session = get_session()
        try:
            repository.get_or_create_user(session, message.from_user.id, message.from_user.username)
        finally:
            session.close()
        bot.send_message(
            message.chat.id,
            "Привет! Это игра «Фейк или Правда». Проверьте свою медиаграмотность: "
            "прочитайте новость и попробуйте определить, достоверна ли она.",
            reply_markup=main_menu()
        )
        send_rules(message.chat.id)

    @bot.message_handler(commands=["help"])
    def help_command(message):
        bot.send_message(message.chat.id,
            "Команды: /start — меню, /play — игра, /stats — статистика, "
            "/reset_progress — сброс просмотренных новостей, /admin — администрирование.")

    @bot.message_handler(commands=["play"])
    def play(message):
        session = get_session()
        try:
            repository.get_or_create_user(session, message.from_user.id, message.from_user.username)
        finally:
            session.close()
        send_round(message.chat.id, message.from_user.id)

    @bot.message_handler(func=lambda m: m.text == "🎮 Играть")
    def play_button(message):
        play(message)

    @bot.message_handler(commands=["stats"])
    @bot.message_handler(func=lambda m: m.text == "📊 Статистика")
    def stats(message):
        session = get_session()
        try:
            repository.get_or_create_user(session, message.from_user.id, message.from_user.username)
            data = repository.get_user_stats(session, message.from_user.id)
        finally:
            session.close()
        bot.send_message(message.chat.id,
            f"<b>Ваша статистика</b>\nРаундов: {data['total']}\n"
            f"Правильных ответов: {data['correct']}\n"
            f"Точность: {data['percent']}%\nТекущая серия: {data['streak']}\n"
            f"Лучшая серия: {data['max_streak']}")

    @bot.message_handler(commands=["reset_progress"])
    def reset_progress(message):
        bot.send_message(message.chat.id, "Сбросить историю просмотренных новостей? "
                        "Журнал ответов и статистика сохранятся.", reply_markup=confirm_reset_keyboard())

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reset:"))
    def reset_callback(call):
        if call.data == "reset:yes":
            session = get_session()
            try:
                repository.reset_seen_news(session, call.from_user.id)
            finally:
                session.close()
            bot.answer_callback_query(call.id, "Прогресс сброшен")
            bot.edit_message_text("История просмотренных новостей очищена. Статистика сохранена.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Сброс отменён")
            bot.edit_message_text("Сброс отменён.", call.message.chat.id, call.message.message_id)

    @bot.callback_query_handler(func=lambda call: call.data == "next")
    def next_news(call):
        bot.answer_callback_query(call.id)
        send_round(call.message.chat.id, call.from_user.id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("answer:"))
    def answer_callback(call):
        try:
            _, choice, news_id, token = call.data.split(":")
            choice_bool = choice == "1"
            news_id = int(news_id)
        except (ValueError, TypeError):
            bot.answer_callback_query(call.id, "Некорректный ответ")
            return
        session = get_session()
        try:
            result, created = submit_answer(session, call.from_user.id, news_id, choice_bool, token)
        except Exception:
            session.rollback()
            logger.exception("Ошибка обработки ответа")
            bot.answer_callback_query(call.id, "Не удалось сохранить ответ")
            bot.send_message(call.message.chat.id, "Произошла ошибка. Попробуйте позже.")
            return
        finally:
            session.close()
        if not created or result is None:
            bot.answer_callback_query(call.id, "Вы уже ответили на этот раунд")
            return
        news, correct = result
        bot.answer_callback_query(call.id, "Ответ принят")
        verdict = "Верно! ✅" if correct else "Неверно. ❌"
        correct_answer = "Фейк" if news.is_fake else "Правда"
        explanation = (
            f"<b>{verdict}</b>\nПравильный ответ: <b>{correct_answer}</b>\n\n"
            f"<b>Пояснение:</b> {escape(news.explanation)}"
        )
        if news.source_url:
            explanation += f'\n\n<a href="{escape(news.source_url, quote=True)}">Источник</a>'
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, explanation, reply_markup=next_keyboard(), disable_web_page_preview=True)

    @bot.message_handler(commands=["admin"])
    def admin(message):
        if message.from_user.id not in settings.admin_ids:
            bot.reply_to(message, "У вас нет доступа к администрированию.")
            return
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Добавить новость", callback_data="admin:add"))
        markup.add(InlineKeyboardButton("Статистика новостей", callback_data="admin:stats"))
        bot.send_message(message.chat.id, "<b>Панель администратора</b>", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin:"))
    def admin_callback(call):
        if call.from_user.id not in settings.admin_ids:
            bot.answer_callback_query(call.id, "Нет доступа")
            return
        action = call.data.split(":")[1]
        bot.answer_callback_query(call.id)
        if action == "add":
            ADMIN_STATES[call.from_user.id] = {"step": "text", "data": {}}
            bot.send_message(call.message.chat.id, "Введите текст новости (20–1000 символов).")
        elif action == "stats":
            session = get_session()
            try:
                data = repository.get_news_stats(session)
            finally:
                session.close()
            text = (f"<b>Новости:</b> {data['total']}\nФейков: {data['fake']}\n"
                    f"Правдивых: {data['real']}\n\n<b>Топ-5 сложных:</b>")
            if not data["hardest"]:
                text += "\nПока недостаточно ответов."
            for item in data["hardest"]:
                text += f"\n#{item['id']} — ошибок {item['error_rate']}% ({item['answers']} ответов)"
            bot.send_message(call.message.chat.id, text)

    @bot.message_handler(commands=["news_stats"])
    def news_stats_command(message):
        if message.from_user.id not in settings.admin_ids:
            bot.reply_to(message, "У вас нет доступа.")
            return
        session = get_session()
        try:
            data = repository.get_news_stats(session)
        finally:
            session.close()
        text = (f"<b>Новости:</b> {data['total']}\nФейков: {data['fake']}\n"
                f"Правдивых: {data['real']}\n\n<b>Топ-5 сложных:</b>")
        if not data["hardest"]:
            text += "\nПока недостаточно ответов."
        for item in data["hardest"]:
            text += f"\n#{item['id']} — ошибок {item['error_rate']}% ({item['answers']} ответов)"
        bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=["add_news"])
    def add_news_command(message):
        if message.from_user.id not in settings.admin_ids:
            bot.reply_to(message, "У вас нет доступа.")
            return
        ADMIN_STATES[message.from_user.id] = {"step": "text", "data": {}}
        bot.reply_to(message, "Введите текст новости (20–1000 символов).")

    @bot.message_handler(func=lambda m: m.from_user.id in ADMIN_STATES, content_types=["text"])
    def admin_dialog(message):
        state = ADMIN_STATES.get(message.from_user.id)
        if not state:
            return
        value = message.text.strip()
        step = state["step"]
        data = state["data"]
        if step == "text":
            if not 20 <= len(value) <= 1000:
                bot.reply_to(message, "Текст должен содержать 20–1000 символов. Повторите ввод.")
                return
            data["text"] = value
            state["step"] = "label"
            bot.reply_to(message, "Это фейк? Введите true/false (или да/нет).")
        elif step == "label":
            normalized = value.lower()
            if normalized not in ("true", "false", "да", "нет"):
                bot.reply_to(message, "Введите строго true/false (можно да/нет).")
                return
            data["is_fake"] = normalized in ("true", "да")
            state["step"] = "explanation"
            bot.reply_to(message, "Введите пояснение (10–500 символов).")
        elif step == "explanation":
            if not 10 <= len(value) <= 500:
                bot.reply_to(message, "Пояснение должно содержать 10–500 символов.")
                return
            data["explanation"] = value
            state["step"] = "source"
            bot.reply_to(message, "Введите ссылку на источник или /skip.")
        elif step == "source":
            data["source_url"] = None if value == "/skip" else value
            state["step"] = "category"
            bot.reply_to(message, "Введите категорию или /skip.")
        elif step == "category":
            data["category"] = None if value == "/skip" else value[:32]
            session = get_session()
            try:
                news = repository.add_news(session, data["text"], data["is_fake"],
                    data["explanation"], data.get("source_url"), data.get("category"))
            except Exception:
                session.rollback()
                logger.exception("Не удалось добавить новость")
                bot.reply_to(message, "Не удалось добавить новость. Проверьте введённые данные.")
                return
            finally:
                session.close()
            ADMIN_STATES.pop(message.from_user.id, None)
            logger.info("Администратор %s добавил новость %s", message.from_user.id, news.id)
            bot.reply_to(message, f"Новость добавлена (id={news.id}).")

    @bot.message_handler(func=lambda m: m.text == "ℹ️ Правила")
    def rules_button(message):
        send_rules(message.chat.id)

    @bot.message_handler(func=lambda m: True)
    def unknown(message):
        bot.reply_to(message, "Неизвестная команда. Используйте /help для списка команд.")

    return bot
