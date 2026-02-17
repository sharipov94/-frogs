from typing import Optional
from aiogram import Bot
from aiogram.types import InputMediaPhoto, CallbackQuery

from app.db.repo import ProductRepo
from app.keyboards.inline import kb_catalog_nav, kb_product, kb_back_to_catalog
from app.services.render_service import render_card_caption, render_details_text


class CatalogService:
    def __init__(self, repo: ProductRepo):
        self._repo = repo

    async def send_catalog_page(self, bot: Bot, chat_id: int, page: int, edit_from: Optional[CallbackQuery] = None):
        total = await self._repo.count_products()
        max_page = max(0, (total - 1) // self._repo._page_size)  # ок для простоты; хочешь — сделаем красиво

        products = await self._repo.get_products_page(page)
        if not products:
            text = "Каталог пуст."
            if edit_from:
                await edit_from.message.edit_text(text)
            else:
                await bot.send_message(chat_id, text)
            return

        header = "Каталог:"
        nav_kb = kb_catalog_nav(page, max_page)
        if edit_from:
            await edit_from.message.edit_text(header, reply_markup=nav_kb)
        else:
            await bot.send_message(chat_id, header, reply_markup=nav_kb)

        for p in products:
            preview_id = await self._repo.get_preview_photo_id(p.id)
            caption = render_card_caption(p)
            if preview_id:
                await bot.send_photo(chat_id, photo=preview_id, caption=caption, reply_markup=kb_product(p.id))
            else:
                await bot.send_message(chat_id, caption, reply_markup=kb_product(p.id))

    async def send_product_details(self, cq: CallbackQuery, product_id: int, back_page: int = 0):
        p = await self._repo.get_product(product_id)
        if not p:
            await cq.message.answer("Товар не найден.")
            return

        photo_ids = await self._repo.get_all_photo_ids(product_id)
        includes = await self._repo.get_includes(product_id)

        if photo_ids:
            media = [InputMediaPhoto(media=pid) for pid in photo_ids[:10]]
            await cq.message.answer_media_group(media)

        details = render_details_text(p, includes)
        await cq.message.answer(details, reply_markup=kb_back_to_catalog(back_page))
