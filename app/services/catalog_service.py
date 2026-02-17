from typing import Optional

from aiogram import Bot
from aiogram.types import CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup

from app.db.repo import ProductRepo
from app.keyboards.inline import (
    kb_catalog_card,
    kb_catalog_footer,
    kb_catalog_nav,
    kb_product_details,
)
from app.services.render_service import render_card_caption, render_details_text


class CatalogService:
    def __init__(self, repo: ProductRepo):
        self._repo = repo

    async def send_catalog_page(
        self,
        bot: Bot,
        chat_id: int,
        page: int,
        is_admin: bool,
        edit_from: Optional[CallbackQuery] = None,
    ):
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
        card_rows = kb_catalog_card(p.id, page).inline_keyboard
        footer = kb_catalog_footer(is_admin)
        reply_markup = InlineKeyboardMarkup(inline_keyboard=card_rows + [nav_row, footer])

        if edit_from:
            message = edit_from.message
            try:
                if preview_id:
                    await message.edit_media(
                        media=InputMediaPhoto(media=preview_id, caption=caption),
                        reply_markup=reply_markup,
                    )
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

    async def send_product_details(self, cq: CallbackQuery, product_id: int, back_page: int, is_admin: bool):
        p = await self._repo.get_product(product_id, include_hidden=bool(is_admin))
        if not p:
            await cq.answer("Товар не найден", show_alert=True)
            return

        includes = await self._repo.get_includes(product_id)
        details = render_details_text(p, includes)
        details_kb = kb_product_details(
            product_id=p.id,
            page=back_page,
            is_admin=is_admin,
            status=p.status,
            is_hidden=p.is_hidden,
        )

        try:
            await cq.message.edit_caption(caption=details, reply_markup=details_kb)
        except Exception:
            try:
                await cq.message.edit_text(details, reply_markup=details_kb)
            except Exception:
                await cq.message.answer(details, reply_markup=details_kb)
