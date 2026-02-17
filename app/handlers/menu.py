# from aiogram import Router, F
# from aiogram.types import Message
# from aiogram.fsm.context import FSMContext

# from app.keyboards.reply import main_menu_kb
# from app.services.catalog_service import CatalogService
# from app.db.repo import ProductRepo


# def bind_menu(service: CatalogService, repo: ProductRepo, admin_ids: tuple[int, ...]) -> Router:
#     r = Router()

#     def is_admin(uid: int) -> bool:
#         return uid in admin_ids

#     @r.message(F.text == "📦 Каталог")
#     async def btn_catalog(m: Message):
#         await service.send_catalog_page(m.bot, m.chat.id, page=0)

#     @r.message(F.text == "➕ Добавить товар")
#     async def btn_add_product(m: Message, state: FSMContext):
#         if not is_admin(m.from_user.id):
#             return
#         # запускаем ту же логику, что /add_product
#         await state.clear()
#         # импорт внутри, чтобы не делать циклические импорты
#         from app.handlers.admin import AddProduct
#         await state.set_state(AddProduct.title)
#         await m.answer("Название товара?")

#     @r.message(F.text == "📋 Товары")
#     async def btn_products(m: Message):
#         if not is_admin(m.from_user.id):
#             return

#         items = await repo.list_products(limit=50)
#         if not items:
#             await m.answer("Товаров пока нет.")
#             return

#         lines = ["Товары (последние 50):"]
#         for p in items:
#             lines.append(f"{p.id}: {p.title} | {p.status} | {p.price}{p.currency}")
#         lines.append("\nЧтобы редактировать/удалить: /edit_product <id> или /delete_product <id>")
#         await m.answer("\n".join(lines))

#     @r.message(F.text == "❌ Отмена")
#     async def btn_cancel(m: Message, state: FSMContext):
#         if not is_admin(m.from_user.id):
#             return
#         await state.clear()
#         await m.answer("Ок, отменил.", reply_markup=main_menu_kb(is_admin=True))

#     return r
