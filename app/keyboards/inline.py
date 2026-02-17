from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def kb_start(is_admin: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="📦 Каталог", callback_data="menu:catalog:0")]]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Админ-команды", callback_data="menu:admin")])
        rows.append([InlineKeyboardButton(text="📨 Заявки", callback_data="menu:orders")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_product(product_id: int, page: int, is_admin: bool = False, status: str = "available", is_hidden: int = 0):
    rows = [[InlineKeyboardButton(text="Подробнее", callback_data=f"product:{product_id}:{page}")]]

    if not is_admin:
        rows.append([InlineKeyboardButton(text="✅ Заказать", callback_data=f"order:{product_id}")])
    else:
        if status == "sold":
            rows.append([InlineKeyboardButton(text="🟢 В наличии", callback_data=f"admin_status:{product_id}:available")])
        else:
            rows.append([InlineKeyboardButton(text="🔴 Распродано", callback_data=f"admin_status:{product_id}:sold")])

        if is_hidden:
            rows.append([InlineKeyboardButton(text="👁 Показать", callback_data=f"admin_hide:{product_id}:0")])
        else:
            rows.append([InlineKeyboardButton(text="🙈 Скрыть", callback_data=f"admin_hide:{product_id}:1")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_catalog_nav(page: int, max_page: int) -> list[InlineKeyboardButton]:
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="← Назад", callback_data=f"catalog:{page-1}"))
    buttons.append(InlineKeyboardButton(text=f"{page+1}/{max_page+1}", callback_data="noop"))
    if page < max_page:
        buttons.append(InlineKeyboardButton(text="Вперёд →", callback_data=f"catalog:{page+1}"))
    return buttons


def kb_back_to_catalog(page: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← В каталог", callback_data=f"catalog:{page}")]
    ])
