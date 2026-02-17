from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from app.services.catalog_service import CatalogService

router = Router()


def bind(service: CatalogService) -> Router:
    r = Router()

    @r.message(Command("catalog"))
    async def catalog(m):
        await service.send_catalog_page(m.bot, m.chat.id, page=0)

    @r.callback_query(F.data.startswith("menu:catalog:"))
    async def catalog_from_menu(cq: CallbackQuery):
        page = int(cq.data.split(":")[-1])
        await service.send_catalog_page(cq.bot, cq.message.chat.id, page=page, edit_from=cq)
        await cq.answer()

    @r.callback_query(F.data.startswith("catalog:"))
    async def catalog_cb(cq: CallbackQuery):
        page = int(cq.data.split(":")[1])
        await service.send_catalog_page(cq.bot, cq.message.chat.id, page=page, edit_from=cq)
        await cq.answer()

    @r.callback_query(F.data.startswith("product:"))
    async def product_cb(cq: CallbackQuery):
        _, pid, page = cq.data.split(":")
        await service.send_product_details(cq, product_id=int(pid), back_page=int(page))
        await cq.answer()

    @r.callback_query(F.data == "noop")
    async def noop(cq: CallbackQuery):
        await cq.answer()

    return r
