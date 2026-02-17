from typing import List, Optional, Tuple
import aiosqlite
from app.models.product import Product
from typing import Optional


class ProductRepo:
    def __init__(self, conn: aiosqlite.Connection, page_size: int):
        self._conn = conn
        self._page_size = page_size

    async def count_products(self) -> int:
        row = await (await self._conn.execute("SELECT COUNT(*) AS c FROM products")).fetchone()
        return int(row["c"])

    async def get_products_page(self, page: int) -> List[Product]:
        offset = page * self._page_size
        rows = await (await self._conn.execute(
            """
            SELECT id, slug, title, description, price, currency, delivery_note, status, status_label
            FROM products
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (self._page_size, offset)
        )).fetchall()

        return [
            Product(
                id=r["id"], slug=r["slug"], title=r["title"], description=r["description"],
                price=r["price"], currency=r["currency"], delivery_note=r["delivery_note"],
                status=r["status"], status_label=r["status_label"]
            ) for r in rows
        ]

    async def get_product(self, product_id: int) -> Optional[Product]:
        r = await (await self._conn.execute(
            """
            SELECT id, slug, title, description, price, currency, delivery_note, status, status_label
            FROM products WHERE id = ?
            """,
            (product_id,)
        )).fetchone()
        if not r:
            return None
        return Product(
            id=r["id"], slug=r["slug"], title=r["title"], description=r["description"],
            price=r["price"], currency=r["currency"], delivery_note=r["delivery_note"],
            status=r["status"], status_label=r["status_label"]
        )

    async def get_preview_photo_id(self, product_id: int) -> Optional[str]:
        r = await (await self._conn.execute(
            """
            SELECT tg_file_id
            FROM product_photos
            WHERE product_id = ?
            ORDER BY is_preview DESC, sort_order ASC, id ASC
            LIMIT 1
            """,
            (product_id,)
        )).fetchone()
        return r["tg_file_id"] if r else None

    async def get_all_photo_ids(self, product_id: int) -> List[str]:
        rows = await (await self._conn.execute(
            """
            SELECT tg_file_id
            FROM product_photos
            WHERE product_id = ?
            ORDER BY is_preview DESC, sort_order ASC, id ASC
            """,
            (product_id,)
        )).fetchall()
        return [r["tg_file_id"] for r in rows]

    async def get_includes(self, product_id: int) -> List[str]:
        rows = await (await self._conn.execute(
            """
            SELECT item_text
            FROM product_includes
            WHERE product_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (product_id,)
        )).fetchall()
        return [r["item_text"] for r in rows]

    async def create_product(
        self,
        slug: str,
        title: str,
        description: str | None,
        price: int,
        currency: str,
        delivery_note: str | None,
        status: str,
        status_label: str | None,
    ) -> int:
        cur = await self._conn.execute(
            """
            INSERT INTO products (slug, title, description, price, currency, delivery_note, status, status_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (slug, title, description, price, currency, delivery_note, status, status_label)
        )
        await self._conn.commit()
        return int(cur.lastrowid)

    async def add_photo(self, product_id: int, tg_file_id: str, sort_order: int = 0, is_preview: bool = False) -> None:
        await self._conn.execute(
            """
            INSERT INTO product_photos (product_id, tg_file_id, sort_order, is_preview)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, tg_file_id, sort_order, 1 if is_preview else 0)
        )
        await self._conn.commit()

    async def add_include(self, product_id: int, item_text: str, sort_order: int = 0) -> None:
        await self._conn.execute(
            """
            INSERT INTO product_includes (product_id, item_text, sort_order)
            VALUES (?, ?, ?)
            """,
            (product_id, item_text, sort_order)
        )
        await self._conn.commit()

    async def list_products(self, limit: int = 50) -> list[Product]:
        rows = await (await self._conn.execute(
            """
            SELECT id, slug, title, description, price, currency, delivery_note, status, status_label
            FROM products
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,)
        )).fetchall()

        return [
            Product(
                id=r["id"], slug=r["slug"], title=r["title"], description=r["description"],
                price=r["price"], currency=r["currency"], delivery_note=r["delivery_note"],
                status=r["status"], status_label=r["status_label"]
            ) for r in rows
        ]

    async def delete_product(self, product_id: int) -> bool:
        cur = await self._conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await self._conn.commit()
        return cur.rowcount > 0

    async def update_product_field(self, product_id: int, field: str, value) -> bool:
        allowed = {"title", "description", "price", "currency", "delivery_note", "status", "status_label"}
        if field not in allowed:
            raise ValueError(f"Field not allowed: {field}")

        cur = await self._conn.execute(
            f"UPDATE products SET {field} = ?, updated_at = datetime('now') WHERE id = ?",
            (value, product_id)
        )
        await self._conn.commit()
        return cur.rowcount > 0