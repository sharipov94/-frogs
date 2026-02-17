from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.config import load_settings
from app.keyboards.inline import kb_admin_panel, kb_start

router = Router()


def _is_admin(user_id: int) -> bool:
    settings = load_settings()
    return user_id in settings.admin_ids


async def _replace_with_text(cq: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    try:
        await cq.message.edit_text(text, reply_markup=markup)
    except Exception:
        try:
            await cq.message.delete()
        except Exception:
            pass
        await cq.message.answer(text, reply_markup=markup)


@router.message(Command("start"))
async def start(m: Message):
    await m.answer("Магазин готов 👇", reply_markup=kb_start(_is_admin(m.from_user.id)))


@router.callback_query(F.data == "menu:home")
async def menu_home(cq: CallbackQuery):
    await _replace_with_text(cq, "Главное меню 👇", kb_start(_is_admin(cq.from_user.id)))
    await cq.answer()


@router.callback_query(F.data == "menu:admin")
async def admin_menu(cq: CallbackQuery):
    if not _is_admin(cq.from_user.id):
        await cq.answer("Нет доступа", show_alert=True)
        return

    await _replace_with_text(
        cq,
        "Админ-панель:\n"
        "• Добавить товар — /add_product\n"
        "• Редактировать — /edit_product <id>\n"
        "• Удалить — /delete_product <id>",
        kb_admin_panel(),
    )
    await cq.answer()
