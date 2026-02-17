from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards.inline import kb_admin_panel, kb_orders_list, kb_product_details


def bind_ui(repo, admin_ids: tuple[int, ...]) -> Router:
    r = Router()

    def is_admin(uid: int):
        return uid in admin_ids

    async def replace_with_text(cq: CallbackQuery, text: str, markup: InlineKeyboardMarkup, parse_mode: str | None = None):
        try:
            await cq.message.edit_text(text, reply_markup=markup, parse_mode=parse_mode)
        except Exception:
            try:
                await cq.message.delete()
            except Exception:
                pass
            await cq.message.answer(text, reply_markup=markup, parse_mode=parse_mode)

    @r.callback_query(F.data == "admin:products")
    async def admin_products(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        items = await repo.list_products(limit=20, include_hidden=True)
        if not items:
            await replace_with_text(cq, "Товаров пока нет.", kb_admin_panel())
            await cq.answer()
            return

        lines = ["Товары (20):"]
        buttons: list[list[InlineKeyboardButton]] = []
        for p in items:
            hidden = "скрыт" if p.is_hidden else "виден"
            lines.append(f"{p.id}: {p.title} | {p.status} | {hidden}")
            buttons.append([InlineKeyboardButton(text=f"Открыть #{p.id}", callback_data=f"product:{p.id}:0")])

        buttons.append([InlineKeyboardButton(text="← Назад", callback_data="menu:admin")])
        await replace_with_text(cq, "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=buttons))
        await cq.answer()

    @r.callback_query(F.data.startswith("admin_status:"))
    async def change_status(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        parts = cq.data.split(":")
        pid = int(parts[1])
        new_status = parts[2]
        page = int(parts[3]) if len(parts) > 3 else 0

        label = "В НАЛИЧИИ" if new_status == "available" else "РАСПРОДАНО"
        await repo.set_status(pid, new_status, label)
        p = await repo.get_product(pid)

        if p:
            await cq.message.edit_reply_markup(
                reply_markup=kb_product_details(p.id, page, True, p.status, p.is_hidden)
            )
        await cq.answer("Статус обновлён")

    @r.callback_query(F.data.startswith("admin_hide:"))
    async def hide_product(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        parts = cq.data.split(":")
        pid = int(parts[1])
        hidden = bool(int(parts[2]))
        page = int(parts[3]) if len(parts) > 3 else 0

        await repo.set_hidden(pid, hidden)
        p = await repo.get_product(pid)

        if p:
            await cq.message.edit_reply_markup(
                reply_markup=kb_product_details(p.id, page, True, p.status, p.is_hidden)
            )
        await cq.answer("Обновлено")

    @r.callback_query(F.data == "menu:orders")
    async def menu_orders(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        rows = await repo.list_order_requests(limit=20)
        if not rows:
            await cq.answer()
            await replace_with_text(cq, "Заявок пока нет.", kb_admin_panel())
            return

        lines = ["Последние заявки:"]
        row_dicts: list[dict] = []
        for row in rows:
            status_label = "new" if row["status"] == "new" else "in_progress" if row["status"] == "in_progress" else "done"
            if row["username"]:
                uname = escape(row["username"])
                contact = f"<a href='https://t.me/{uname}'>@{uname}</a>"
            else:
                contact_name = escape(row["first_name"] or "пользователь")
                contact = f"<a href='tg://user?id={row['user_id']}'>{contact_name}</a>"

            lines.append(f"#{row['id']} [{status_label}] | {escape(row['title'])} | {contact} | {row['created_at']}")
            row_dicts.append(dict(row))

        await cq.answer()
        await replace_with_text(cq, "\n".join(lines), kb_orders_list(row_dicts), parse_mode="HTML")

    @r.callback_query(F.data.startswith("orderstatus:"))
    async def update_order_status(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        _, order_id, new_status = cq.data.split(":")
        ok = await repo.set_order_status(int(order_id), new_status)
        if not ok:
            await cq.answer("Заявка не найдена", show_alert=True)
            return

        await cq.answer("Статус заявки обновлён")
        await menu_orders(cq)

    @r.callback_query(F.data.startswith("order:"))
    async def order_product(cq: CallbackQuery):
        pid = int(cq.data.split(":")[1])
        product = await repo.get_product(pid, include_hidden=False)
        if not product:
            await cq.answer("Товар недоступен", show_alert=True)
            return

        await repo.create_order_request(
            product_id=pid,
            user_id=cq.from_user.id,
            username=cq.from_user.username,
            first_name=cq.from_user.first_name,
        )
        await cq.answer("Заявка отправлена ✅", show_alert=True)

    return r
