from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.config import load_settings
from app.keyboards.inline import kb_start

router = Router()


@router.message(Command("start"))
async def start(m: Message):
    settings = load_settings()
    is_admin = m.from_user.id in settings.admin_ids
    await m.answer("Магазин готов 👇", reply_markup=kb_start(is_admin))


@router.callback_query(F.data == "menu:admin")
async def admin_menu(cq: CallbackQuery):
    settings = load_settings()
    if cq.from_user.id not in settings.admin_ids:
        await cq.answer("Нет доступа", show_alert=True)
        return

    await cq.message.edit_text(
        "Админ-команды:\n"
        "/add_product — добавить товар\n"
        "/products — список товаров\n"
        "/edit_product <id> — редактировать\n"
        "/delete_product <id> — удалить\n"
        "/orders — заявки",
        reply_markup=kb_start(is_admin=True),
    )
    await cq.answer()
