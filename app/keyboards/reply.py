from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_kb(is_admin: bool) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text="📦 Каталог")]]

    if is_admin:
        rows.extend(
            [
                [KeyboardButton(text="🛠 Админ-панель")],
                [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="📋 Товары")],
                [KeyboardButton(text="📨 Заявки")],
            ]
        )

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
