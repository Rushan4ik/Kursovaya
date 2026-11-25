from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🎮 Играть"), KeyboardButton("📊 Статистика"))
    markup.row(KeyboardButton("ℹ️ Правила"))
    return markup


def game_keyboard(news_id: int, token: str):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🟥 Фейк", callback_data=f"answer:1:{news_id}:{token}"),
        InlineKeyboardButton("🟩 Правда", callback_data=f"answer:0:{news_id}:{token}")
    )
    return markup


def next_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Следующая новость", callback_data="next"))
    return markup


def confirm_reset_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Да, сбросить", callback_data="reset:yes"),
        InlineKeyboardButton("Отмена", callback_data="reset:no")
    )
    return markup
