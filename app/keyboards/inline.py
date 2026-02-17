from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def kb_start(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📦 Каталог", callback_data="menu:catalog:0")]]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="menu:admin")])
        rows.append([InlineKeyboardButton(text="📨 Заявки", callback_data="menu:orders")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Товары", callback_data="admin:products")],
            [InlineKeyboardButton(text="📨 Заявки", callback_data="menu:orders")],
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add")],
            [InlineKeyboardButton(text="← В меню", callback_data="menu:home")],
        ]
    )


def kb_orders_list(rows: list[dict]) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    for row in rows:
        current = row["status"]
        nxt = "in_progress" if current == "new" else "done" if current == "in_progress" else "new"
        title = "Новая" if current == "new" else "В работе" if current == "in_progress" else "Завершена"
        buttons.append([
            InlineKeyboardButton(text=f"#{row['id']} • {title}", callback_data=f"orderstatus:{row['id']}:{nxt}")
        ])

    buttons.append([InlineKeyboardButton(text="← В админ-панель", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_catalog_card(product_id: int, page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Подробнее", callback_data=f"product:{product_id}:{page}")]]
    )


def kb_catalog_nav(page: int, max_page: int) -> list[InlineKeyboardButton]:
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="← Назад", callback_data=f"catalog:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page+1}/{max_page+1}", callback_data="noop"))
    if page < max_page:
        buttons.append(InlineKeyboardButton(text="Вперёд →", callback_data=f"catalog:{page+1}"))
    return buttons


def kb_catalog_footer(is_admin: bool) -> list[InlineKeyboardButton]:
    row = [InlineKeyboardButton(text="← В меню", callback_data="menu:home")]
    if is_admin:
        row.append(InlineKeyboardButton(text="🛠 Админ", callback_data="menu:admin"))
    return row


def kb_product_details(
    product_id: int,
    page: int,
    is_admin: bool,
    status: str = "available",
    is_hidden: int = 0,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if not is_admin:
        rows.append([InlineKeyboardButton(text="✅ Заказать", callback_data=f"order:{product_id}")])
    else:
        rows.append([InlineKeyboardButton(text="✏️ Изменить", callback_data=f"admin_edit_start:{product_id}")])
        rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete:{product_id}")])

        if status == "sold":
            rows.append([InlineKeyboardButton(text="🟢 В наличии", callback_data=f"admin_status:{product_id}:available:{page}")])
        else:
            rows.append([InlineKeyboardButton(text="🔴 Распродано", callback_data=f"admin_status:{product_id}:sold:{page}")])

        if is_hidden:
            rows.append([InlineKeyboardButton(text="👁 Показать", callback_data=f"admin_hide:{product_id}:0:{page}")])
        else:
            rows.append([InlineKeyboardButton(text="🙈 Скрыть", callback_data=f"admin_hide:{product_id}:1:{page}")])

    rows.append([InlineKeyboardButton(text="← В каталог", callback_data=f"catalog:{page}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
