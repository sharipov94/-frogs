from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.inline import kb_product


def bind_ui(repo, admin_ids: tuple[int, ...]) -> Router:
    r = Router()

    def is_admin(uid: int):
        return uid in admin_ids

    @r.callback_query(F.data.startswith("admin_status:"))
    async def change_status(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        _, pid, new_status = cq.data.split(":")
        pid = int(pid)

        label = "В НАЛИЧИИ" if new_status == "available" else "РАСПРОДАНО"
        await repo.set_status(pid, new_status, label)
        p = await repo.get_product(pid)

        if p:
            await cq.message.edit_reply_markup(
                reply_markup=kb_product(p.id, True, p.status, p.is_hidden)
            )
        await cq.answer("Статус обновлён")

    @r.callback_query(F.data.startswith("admin_hide:"))
    async def hide_product(cq: CallbackQuery):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        _, pid, hidden = cq.data.split(":")
        pid = int(pid)
        hidden = bool(int(hidden))

        await repo.set_hidden(pid, hidden)
        p = await repo.get_product(pid)

        if p:
            await cq.message.edit_reply_markup(
                reply_markup=kb_product(p.id, True, p.status, p.is_hidden)
            )
        await cq.answer("Обновлено")

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
