from typing import Optional

from aiogram import Bot
from aiogram.types import CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup

from app.db.repo import ProductRepo
from app.keyboards.inline import kb_back_to_catalog, kb_catalog_nav, kb_product
from app.services.render_service import render_card_caption, render_details_text


class CatalogService:
    def __init__(self, repo: ProductRepo):
        self._repo = repo

    async def send_catalog_page(self, bot: Bot, chat_id: int, page: int, edit_from: Optional[CallbackQuery] = None):
        total = await self._repo.count_products(include_hidden=False)
        if total == 0:
            text = "Каталог пуст."
            if edit_from:
                await edit_from.message.edit_text(text)
            else:
                await bot.send_message(chat_id, text)
            return

        max_page = max(0, total - 1)
        page = min(max(page, 0), max_page)

        p = await self._repo.get_product_by_offset(page, include_hidden=False)
        if not p:
            if edit_from:
                await edit_from.message.edit_text("Каталог пуст.")
            else:
                await bot.send_message(chat_id, "Каталог пуст.")
            return
        preview_id = await self._repo.get_preview_photo_id(p.id)
        caption = render_card_caption(p)

        nav_row = kb_catalog_nav(page, max_page)
        product_kb = kb_product(p.id, page=page, is_admin=False)
        rows = product_kb.inline_keyboard + [nav_row]
        reply_markup = InlineKeyboardMarkup(inline_keyboard=rows)

        if edit_from:
            message = edit_from.message
            try:
                if preview_id:
                    media = InputMediaPhoto(media=preview_id, caption=caption)
                    await message.edit_media(media=media, reply_markup=reply_markup)
                else:
                    await message.edit_text(caption, reply_markup=reply_markup)
            except Exception:
                if preview_id:
                    await message.delete()
                    await bot.send_photo(chat_id, photo=preview_id, caption=caption, reply_markup=reply_markup)
                else:
                    await message.edit_text(caption, reply_markup=reply_markup)
            return

        if preview_id:
            await bot.send_photo(chat_id, photo=preview_id, caption=caption, reply_markup=reply_markup)
        else:
            await bot.send_message(chat_id, caption, reply_markup=reply_markup)

    async def send_product_details(self, cq: CallbackQuery, product_id: int, back_page: int = 0):
        p = await self._repo.get_product(product_id, include_hidden=False)
        if not p:
            await cq.answer("Товар не найден", show_alert=True)
            return

        includes = await self._repo.get_includes(product_id)
        details = render_details_text(p, includes)

        try:
            await cq.message.edit_caption(caption=details, reply_markup=kb_back_to_catalog(back_page))
        except Exception:
            try:
                await cq.message.edit_text(details, reply_markup=kb_back_to_catalog(back_page))
            except Exception:
                await cq.message.answer(details, reply_markup=kb_back_to_catalog(back_page))
