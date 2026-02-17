from typing import Optional

import aiosqlite

from app.models.product import Product


class ProductRepo:
    def __init__(self, conn: aiosqlite.Connection, page_size: int):
        self._conn = conn
        self._page_size = page_size

    async def count_products(self, include_hidden: bool = False) -> int:
        query = "SELECT COUNT(*) AS c FROM products"
        params: tuple = ()
        if not include_hidden:
            query += " WHERE is_hidden = 0"
        row = await (await self._conn.execute(query, params)).fetchone()
        return int(row["c"])

    async def get_products_page(self, page: int, include_hidden: bool = False) -> list[Product]:
        offset = page * self._page_size
        query = """
            SELECT id, slug, title, description, price, currency, delivery_note, status, status_label, is_hidden
            FROM products
        """
        params: tuple = ()
        if not include_hidden:
            query += " WHERE is_hidden = 0"

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params = (*params, self._page_size, offset)

        rows = await (await self._conn.execute(query, params)).fetchall()
        return [
            Product(
                id=r["id"],
                slug=r["slug"],
                title=r["title"],
                description=r["description"],
                price=r["price"],
                currency=r["currency"],
                delivery_note=r["delivery_note"],
                status=r["status"],
                status_label=r["status_label"],
                is_hidden=r["is_hidden"],
            )
            for r in rows
        ]

    async def get_product(self, product_id: int, include_hidden: bool = True) -> Optional[Product]:
        query = """
            SELECT id, slug, title, description, price, currency, delivery_note, status, status_label, is_hidden
            FROM products
            WHERE id = ?
        """
        params: tuple = (product_id,)
        if not include_hidden:
            query += " AND is_hidden = 0"

        r = await (await self._conn.execute(query, params)).fetchone()
        if not r:
            return None
        return Product(
            id=r["id"],
            slug=r["slug"],
            title=r["title"],
            description=r["description"],
            price=r["price"],
            currency=r["currency"],
            delivery_note=r["delivery_note"],
            status=r["status"],
            status_label=r["status_label"],
            is_hidden=r["is_hidden"],
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
            (product_id,),
        )).fetchone()
        return r["tg_file_id"] if r else None

    async def get_all_photo_ids(self, product_id: int) -> list[str]:
        rows = await (await self._conn.execute(
            """
            SELECT tg_file_id
            FROM product_photos
            WHERE product_id = ?
            ORDER BY is_preview DESC, sort_order ASC, id ASC
            """,
            (product_id,),
        )).fetchall()
        return [r["tg_file_id"] for r in rows]

    async def get_includes(self, product_id: int) -> list[str]:
        rows = await (await self._conn.execute(
            """
            SELECT item_text
            FROM product_includes
            WHERE product_id = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (product_id,),
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
            (slug, title, description, price, currency, delivery_note, status, status_label),
        )
        await self._conn.commit()
        return int(cur.lastrowid)

    async def add_photo(self, product_id: int, tg_file_id: str, sort_order: int = 0, is_preview: bool = False) -> None:
        await self._conn.execute(
            """
            INSERT INTO product_photos (product_id, tg_file_id, sort_order, is_preview)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, tg_file_id, sort_order, 1 if is_preview else 0),
        )
        await self._conn.commit()

    async def add_include(self, product_id: int, item_text: str, sort_order: int = 0) -> None:
        await self._conn.execute(
            """
            INSERT INTO product_includes (product_id, item_text, sort_order)
            VALUES (?, ?, ?)
            """,
            (product_id, item_text, sort_order),
        )
        await self._conn.commit()

    async def list_products(self, limit: int = 50, include_hidden: bool = True) -> list[Product]:
        query = """
            SELECT id, slug, title, description, price, currency, delivery_note, status, status_label, is_hidden
            FROM products
        """
        params: tuple = ()
        if not include_hidden:
            query += " WHERE is_hidden = 0"
        query += " ORDER BY created_at DESC LIMIT ?"
        params = (*params, limit)

        rows = await (await self._conn.execute(query, params)).fetchall()
        return [
            Product(
                id=r["id"],
                slug=r["slug"],
                title=r["title"],
                description=r["description"],
                price=r["price"],
                currency=r["currency"],
                delivery_note=r["delivery_note"],
                status=r["status"],
                status_label=r["status_label"],
                is_hidden=r["is_hidden"],
            )
            for r in rows
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
            (value, product_id),
        )
        await self._conn.commit()
        return cur.rowcount > 0

    async def set_hidden(self, product_id: int, is_hidden: bool) -> bool:
        cur = await self._conn.execute(
            "UPDATE products SET is_hidden = ?, updated_at = datetime('now') WHERE id = ?",
            (1 if is_hidden else 0, product_id),
        )
        await self._conn.commit()
        return cur.rowcount > 0

    async def set_status(self, product_id: int, status: str, status_label: Optional[str] = None) -> bool:
        cur = await self._conn.execute(
            "UPDATE products SET status = ?, status_label = ?, updated_at = datetime('now') WHERE id = ?",
            (status, status_label, product_id),
        )
        await self._conn.commit()
        return cur.rowcount > 0

    async def create_order_request(
        self,
        product_id: int,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
    ) -> None:
        await self._conn.execute(
            """
            INSERT INTO orders_requests (product_id, user_id, username, first_name)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, user_id, username, first_name),
        )
        await self._conn.commit()

    async def list_order_requests(self, limit: int = 30) -> list[aiosqlite.Row]:
        rows = await (await self._conn.execute(
            """
            SELECT o.id, o.product_id, o.user_id, o.username, o.first_name, o.status, o.created_at, p.title
            FROM orders_requests o
            JOIN products p ON p.id = o.product_id
            ORDER BY o.created_at DESC
            LIMIT ?
            """,
            (limit,),
        )).fetchall()
        return rows
