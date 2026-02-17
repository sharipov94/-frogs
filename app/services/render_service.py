from app.models.product import Product


def status_to_label(p: Product) -> str:
    if p.status_label:
        return p.status_label
    mapping = {"available": "В НАЛИЧИИ", "reserved": "БРОНЬ", "sold": "ВЫКУПЛЕНО"}
    return mapping.get(p.status, p.status.upper())


def render_card_caption(p: Product) -> str:
    parts = [status_to_label(p), "", p.title]
    if p.description:
        parts.append(p.description)
    parts.append("")
    delivery = f" {p.delivery_note}" if p.delivery_note else ""
    parts.append(f"Цена: {p.price} {p.currency}{delivery}")
    parts.append(f"Статус: {status_to_label(p)}")
    return "\n".join(parts)


def render_details_text(p: Product, includes: list[str]) -> str:
    lines = [p.title]
    if p.description:
        lines.append(p.description)
    lines.append("")
    if includes:
        lines.append("В комплекте входит:")
        for it in includes:
            lines.append(f"• {it}")
        lines.append("")
    delivery = f" {p.delivery_note}" if p.delivery_note else ""
    lines.append(f"Цена: {p.price} {p.currency}{delivery}")
    lines.append(f"Статус: {status_to_label(p)}")
    return "\n".join(lines)
