import re
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


from app.db.repo import ProductRepo
from app.keyboards.inline import kb_admin_panel


def _slugify(text: str) -> str:
    """
    Простой slug: латиница/цифры/подчёркивания.
    Если из русского ничего не получилось — вернём 'item'.
    """
    s = text.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]+", "", s)
    if not s:
        s = "item"
    return s[:50]

def kb_edit_fields(product_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="Название", callback_data=f"editfield:{product_id}:title")],
        [InlineKeyboardButton(text="Описание", callback_data=f"editfield:{product_id}:description")],
        [InlineKeyboardButton(text="Цена", callback_data=f"editfield:{product_id}:price")],
        [InlineKeyboardButton(text="Доставка", callback_data=f"editfield:{product_id}:delivery_note")],
        [InlineKeyboardButton(text="Статус", callback_data=f"editfield:{product_id}:status")],
        [InlineKeyboardButton(text="Текст статуса", callback_data=f"editfield:{product_id}:status_label")],
        [InlineKeyboardButton(text="Отмена", callback_data="editcancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)



class AddProduct(StatesGroup):
    title = State()
    description = State()
    price = State()
    delivery_note = State()
    status = State()
    status_label = State()
    preview_photo = State()
    extra_photos = State()

class EditProduct(StatesGroup):
    choose_field = State()
    enter_value = State()



def bind_admin(repo: ProductRepo, admin_ids: tuple[int, ...]) -> Router:
    r = Router()

    def is_admin(user_id: int) -> bool:
        return user_id in admin_ids

    # -------------------------
    # HELP / FILE_ID
    # -------------------------
    @r.message(Command("admin"))
    async def admin_help(m: Message):
        if not is_admin(m.from_user.id):
            return
        await m.answer(
            "Админ-команды:\n"
            "/add_product — добавить товар\n"
            "/fileid — получить file_id фото (просто пришли фото)\n"
            "/cancel — отмена мастера\n"
            "/done — завершить добавление фото"
        )

    @r.message(Command("fileid"))
    async def fileid_hint(m: Message):
        if not is_admin(m.from_user.id):
            return
        await m.answer("Пришли мне фото (НЕ как файл), я верну его file_id.")

    # ВАЖНО: выдаём file_id только когда FSM НЕ активен
    @r.message(StateFilter(None), F.photo)
    async def fileid_photo(m: Message):
        if not is_admin(m.from_user.id):
            return
        fid = m.photo[-1].file_id
        await m.answer(f"file_id:\n{fid}")

    # -------------------------
    # CANCEL
    # -------------------------
    @r.message(Command("cancel"))
    async def cancel(m: Message, state: FSMContext):
        if not is_admin(m.from_user.id):
            return
        await state.clear()
        await m.answer("Ок, отменил текущий ввод.", reply_markup=kb_admin_panel())

    # -------------------------
    # ADD PRODUCT WIZARD
    # -------------------------
    @r.message(Command("add_product"))
    async def add_product_start(m: Message, state: FSMContext):
        if not is_admin(m.from_user.id):
            return
        await state.clear()
        await state.set_state(AddProduct.title)
        await m.answer("Название товара?")

    @r.callback_query(F.data == "admin:add")
    async def add_product_start_cb(cq: CallbackQuery, state: FSMContext):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return
        await state.clear()
        await state.set_state(AddProduct.title)
        await cq.answer()
        await cq.message.answer("Название товара?")

    @r.message(AddProduct.title, F.text)
    async def add_product_title(m: Message, state: FSMContext):
        title = m.text.strip()
        await state.update_data(title=title)
        await state.set_state(AddProduct.description)
        await m.answer("Описание? (или '-' чтобы пропустить)")

    @r.message(AddProduct.description, F.text)
    async def add_product_description(m: Message, state: FSMContext):
        text = m.text.strip()
        desc = None if text == "-" else text
        await state.update_data(description=desc)
        await state.set_state(AddProduct.price)
        await m.answer("Цена числом (например 3400)")

    @r.message(AddProduct.price, F.text)
    async def add_product_price(m: Message, state: FSMContext):
        raw = m.text.strip().replace(" ", "")
        if not raw.isdigit():
            await m.answer("Нужно число. Пример: 3400")
            return
        await state.update_data(price=int(raw), currency="₽")
        await state.set_state(AddProduct.delivery_note)
        await m.answer("Подпись доставки? (например '+ доставка' или '-' чтобы пропустить)")

    @r.message(AddProduct.delivery_note, F.text)
    async def add_product_delivery(m: Message, state: FSMContext):
        text = m.text.strip()
        note = None if text == "-" else text
        await state.update_data(delivery_note=note)
        await state.set_state(AddProduct.status)
        await m.answer("Статус: available / reserved / sold")

    @r.message(AddProduct.status, F.text)
    async def add_product_status(m: Message, state: FSMContext):
        s = m.text.strip().lower()
        if s not in {"available", "reserved", "sold"}:
            await m.answer("Только: available / reserved / sold")
            return
        await state.update_data(status=s)
        await state.set_state(AddProduct.status_label)
        await m.answer("Текст статуса на карточке (например 'В НАЛИЧИИ' / 'ВЫКУПЛЕНА') или '-' чтобы авто")

    @r.message(AddProduct.status_label, F.text)
    async def add_product_status_label(m: Message, state: FSMContext):
        text = m.text.strip()
        label = None if text == "-" else text
        await state.update_data(status_label=label)

        data = await state.get_data()
        title = data["title"]
        slug = _slugify(title)

        base = slug
        n = 1
        while True:
            try:
                product_id = await repo.create_product(
                    slug=slug,
                    title=title,
                    description=data.get("description"),
                    price=data["price"],
                    currency=data.get("currency", "₽"),
                    delivery_note=data.get("delivery_note"),
                    status=data["status"],
                    status_label=label,
                )
                break
            except Exception:
                n += 1
                slug = f"{base}_{n}"

        await state.update_data(product_id=product_id, photo_sort=0)
        await state.set_state(AddProduct.preview_photo)
        await m.answer("Теперь пришли ПРЕВЬЮ-фото (одно фото сообщением).")

    # -------------------------
    # PREVIEW PHOTO
    # -------------------------
    @r.message(AddProduct.preview_photo, F.photo)
    async def add_product_preview_photo(m: Message, state: FSMContext):
        data = await state.get_data()
        product_id = data["product_id"]
        fid = m.photo[-1].file_id

        await repo.add_photo(product_id=product_id, tg_file_id=fid, sort_order=0, is_preview=True)

        await state.update_data(photo_sort=1)
        await state.set_state(AddProduct.extra_photos)
        await m.answer(
            "Ок. Теперь можешь присылать остальные фото товара (сколько нужно).\n"
            "Когда закончишь — /done\n"
            "Если хочешь без доп. фото — сразу /done"
        )

    @r.message(AddProduct.preview_photo)
    async def add_product_preview_wrong(m: Message):
        await m.answer("Нужно именно фото (не файл). Пришли превью-фото.")

    # -------------------------
    # EXTRA PHOTOS + DONE
    # -------------------------
    @r.message(AddProduct.extra_photos, Command("done"))
    async def add_product_done(m: Message, state: FSMContext):
        data = await state.get_data()
        pid = data["product_id"]
        await state.clear()
        await m.answer(f"Готово! Товар добавлен. product_id={pid}\nПроверяй /catalog", reply_markup=kb_admin_panel())

    @r.message(AddProduct.extra_photos, F.photo)
    async def add_product_extra_photo(m: Message, state: FSMContext):
        data = await state.get_data()
        product_id = data["product_id"]
        sort_order = int(data.get("photo_sort", 1))
        fid = m.photo[-1].file_id

        await repo.add_photo(product_id=product_id, tg_file_id=fid, sort_order=sort_order, is_preview=False)
        await state.update_data(photo_sort=sort_order + 1)

        await m.answer(f"Фото добавлено ({sort_order}). /done чтобы завершить")

    @r.message(Command("products"))
    async def products_list(m: Message):
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
        lines.append("Команды: /edit_product <id> , /delete_product <id>")
        await m.answer("\n".join(lines))

    @r.message(Command("delete_product"))
    async def delete_product_cmd(m: Message):
        if not is_admin(m.from_user.id):
            return

        parts = (m.text or "").split()
        if len(parts) != 2 or not parts[1].isdigit():
            await m.answer("Использование: /delete_product <id>")
            return

        pid = int(parts[1])
        ok = await repo.delete_product(pid)
        await m.answer("Удалено." if ok else "Не найдено.")


    @r.message(Command("orders"))
    async def orders_list(m: Message):
        if not is_admin(m.from_user.id):
            return

        rows = await repo.list_order_requests(limit=30)
        if not rows:
            await m.answer("Заявок пока нет.")
            return

        lines = ["Последние заявки:"]
        for row in rows:
            username = f"@{row['username']}" if row["username"] else row["first_name"] or "без имени"
            lines.append(f"#{row['id']} | {row['title']} | {username} | {row['created_at']}")
        await m.answer("\n".join(lines))

    async def _start_edit_flow(state: FSMContext, pid: int):
        await state.clear()
        await state.update_data(edit_product_id=pid)
        await state.set_state(EditProduct.choose_field)

    @r.message(Command("edit_product"))
    async def edit_product_cmd(m: Message, state: FSMContext):
        if not is_admin(m.from_user.id):
            return

        parts = (m.text or "").split()
        if len(parts) != 2 or not parts[1].isdigit():
            await m.answer("Использование: /edit_product <id>")
            return

        pid = int(parts[1])
        p = await repo.get_product(pid)
        if not p:
            await m.answer("Товар не найден.")
            return

        await _start_edit_flow(state, pid)
        await m.answer(
            f"Редактируем товар #{pid}: {p.title}\nВыбери поле:",
            reply_markup=kb_edit_fields(pid)
        )

    @r.callback_query(F.data.startswith("admin_edit_start:"))
    async def edit_product_from_card(cq: CallbackQuery, state: FSMContext):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        pid = int(cq.data.split(":")[1])
        p = await repo.get_product(pid)
        if not p:
            await cq.answer("Товар не найден", show_alert=True)
            return

        await _start_edit_flow(state, pid)
        await cq.answer()
        await cq.message.answer(
            f"Редактируем товар #{pid}: {p.title}\nВыбери поле:",
            reply_markup=kb_edit_fields(pid)
        )

    @r.callback_query(F.data.startswith("editfield:"))
    async def edit_choose_field(cq: CallbackQuery, state: FSMContext):
        if not is_admin(cq.from_user.id):
            await cq.answer("Нет доступа", show_alert=True)
            return

        _, pid_str, field = cq.data.split(":")
        pid = int(pid_str)

        await state.update_data(edit_product_id=pid, edit_field=field)
        await state.set_state(EditProduct.enter_value)

        prompts = {
            "title": "Введи новое название:",
            "description": "Введи новое описание (или '-' чтобы очистить):",
            "price": "Введи новую цену числом (например 3400):",
            "delivery_note": "Введи доставку (например '+ доставка' или '-' чтобы очистить):",
            "status": "Введи статус: available / reserved / sold",
            "status_label": "Введи текст статуса (или '-' чтобы авто/очистить):",
        }
        await cq.message.answer(prompts.get(field, "Введи новое значение:"))
        await cq.answer()

    @r.callback_query(F.data == "editcancel")
    async def edit_cancel_cb(cq: CallbackQuery, state: FSMContext):
        if not is_admin(cq.from_user.id):
            return
        await state.clear()
        await cq.answer()
        await cq.message.answer("Ок, отменил редактирование.", reply_markup=kb_admin_panel())

    @r.message(EditProduct.enter_value, F.text)
    async def edit_enter_value(m: Message, state: FSMContext):
        if not is_admin(m.from_user.id):
            return

        data = await state.get_data()
        pid = int(data["edit_product_id"])
        field = data["edit_field"]
        text = (m.text or "").strip()

        # валидация/приведение типов
        if field == "price":
            raw = text.replace(" ", "")
            if not raw.isdigit():
                await m.answer("Цена должна быть числом. Пример: 3400")
                return
            value = int(raw)
        elif field in {"description", "delivery_note", "status_label"}:
            value = None if text == "-" else text
        elif field == "status":
            s = text.lower()
            if s not in {"available", "reserved", "sold"}:
                await m.answer("Только: available / reserved / sold")
                return
            value = s
        else:
            value = text

        ok = await repo.update_product_field(pid, field, value)
        await state.clear()

        if not ok:
            await m.answer("Не удалось обновить (возможно товар удалён).")
            return

        p = await repo.get_product(pid)
        await m.answer(
            f"Готово. Обновлено поле {field} у товара #{pid}.\n"
            f"{p.title} | {p.status} | {p.price}{p.currency}",
            reply_markup=kb_admin_panel()
        )

    return r
