from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from app.services.catalog_service import CatalogService

router = Router()


def bind(service: CatalogService) -> Router:
    # создаём роутер с замыканием на service (просто и чисто)
    r = Router()

    @r.message(F.text == "📦 Каталог")
    async def catalog_btn(m: Message):
        await service.send_catalog_page(m.bot, m.chat.id, page=0)

    @r.message(Command("catalog"))
    async def catalog(m: Message):
        await service.send_catalog_page(m.bot, m.chat.id, page=0)

    @r.callback_query(F.data.startswith("catalog:"))
    async def catalog_cb(cq: CallbackQuery):
        page = int(cq.data.split(":")[1])
        await cq.answer()
        await service.send_catalog_page(cq.bot, cq.message.chat.id, page=page, edit_from=cq)

    @r.callback_query(F.data.startswith("product:"))
    async def product_cb(cq: CallbackQuery):
        product_id = int(cq.data.split(":")[1])
        await cq.answer()
        await service.send_product_details(cq, product_id=product_id, back_page=0)

    @r.callback_query(F.data == "noop")
    async def noop(cq: CallbackQuery):
        await cq.answer()

    return r
