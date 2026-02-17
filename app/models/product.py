from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Product:
    id: int
    slug: str
    title: str
    description: Optional[str]
    price: int
    currency: str
    delivery_note: Optional[str]
    status: str
    status_label: Optional[str]
    is_hidden: int = 0
