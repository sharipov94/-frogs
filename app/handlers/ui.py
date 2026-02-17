from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.keyboards.inline import kb_product


def bind_ui(repo, admin_ids: tuple[int, ...]) -> Router:
    r = Router()

    def is_admin(uid: int):
        return uid in admin_ids

    # Переключение статуса
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

        await cq.answer("Статус обновлён")
        await cq.message.edit_reply_markup(
            reply_markup=kb_product(
                p.id,
                True,
                p.status,
                p.is_hidden
            )
        )

    # Скрыть / Показать
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

        await cq.answer("Обновлено")
        await cq.message.edit_reply_markup(
            reply_markup=kb_product(
                p.id,
                True,
                p.status,
                p.is_hidden
            )
        )

    # Заказ
    @r.callback_query(F.data.startswith("order:"))
    async def order_product(cq: CallbackQuery):
        pid = int(cq.data.split(":")[1])

        await repo._conn.execute(
            "INSERT INTO orders_requests (product_id, user_id, username) VALUES (?, ?, ?)",
            (pid, cq.from_user.id, cq.from_user.username)
        )
        await repo._conn.commit()

        await cq.answer("Заявка отправлена ✅", show_alert=True)

    return r
