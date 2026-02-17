from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.keyboards.reply import main_menu_kb
from app.config import load_settings

router = Router()


@router.message(Command("start"))
async def start(m: Message):
    settings = load_settings()
    is_admin = m.from_user.id in settings.admin_ids
    await m.answer(
        "Меню готово. Выбирай действие кнопками 👇",
        reply_markup=main_menu_kb(is_admin)
    )
