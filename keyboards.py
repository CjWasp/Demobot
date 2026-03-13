from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Уроки"), KeyboardButton(text="📊 Прогресс")],
        ],
        resize_keyboard=True
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Студенты"), KeyboardButton(text="📈 Статистика")],
            [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="🔙 Выйти из админки")],
        ],
        resize_keyboard=True
    )
