from aiogram import F, Router
from aiogram.types import Message

from app.db.repo import ProductRepo
from app.services.catalog_service import CatalogService


def bind_menu(service: CatalogService, repo: ProductRepo, admin_ids: tuple[int, ...]) -> Router:
    r = Router()

    def is_admin(uid: int) -> bool:
        return uid in admin_ids

    @r.message(F.text == "📦 Каталог")
    async def btn_catalog(m: Message):
        await service.send_catalog_page(m.bot, m.chat.id, page=0)

    @r.message(F.text == "🛠 Админ-панель")
    async def admin_panel(m: Message):
        if not is_admin(m.from_user.id):
            return
        await m.answer(
            "Админ-панель:\n"
            "/add_product — добавить товар\n"
            "/products — список товаров\n"
            "/edit_product <id> — редактировать\n"
            "/delete_product <id> — удалить\n"
            "/orders — заявки"
        )

    @r.message(F.text == "📋 Товары")
    async def btn_products(m: Message):
        if not is_admin(m.from_user.id):
            return

        items = await repo.list_products(limit=50)
        if not items:
            await m.answer("Товаров пока нет.")
            return

        lines = ["Товары (последние 50):"]
        for p in items:
            hidden = "скрыт" if p.is_hidden else "виден"
            lines.append(f"{p.id}: {p.title} | {p.status} | {p.price}{p.currency} | {hidden}")
        await m.answer("\n".join(lines))

    @r.message(F.text == "📨 Заявки")
    async def btn_orders(m: Message):
        if not is_admin(m.from_user.id):
            return
        rows = await repo.list_order_requests(limit=20)
        if not rows:
            await m.answer("Заявок пока нет.")
            return

        lines = ["Последние заявки:"]
        for row in rows:
            username = f"@{row['username']}" if row["username"] else row["first_name"] or "без имени"
            lines.append(f"#{row['id']} | {row['title']} | {username} | {row['created_at']}")
        await m.answer("\n".join(lines))

    return r
