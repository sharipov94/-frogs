from pathlib import Path
from typing import Optional

import aiosqlite


class Db:
    def __init__(self, path: str):
        self._path = path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON;")
        await self._ensure_schema()

    async def _ensure_schema(self) -> None:
        if self._conn is None:
            raise RuntimeError("DB is not connected")

        schema_path = Path(__file__).with_name("schema.sql")
        schema_sql = schema_path.read_text(encoding="utf-8")
        await self._conn.executescript(schema_sql)

        cols = await (await self._conn.execute("PRAGMA table_info(products)")).fetchall()
        col_names = {row["name"] for row in cols}
        if "is_hidden" not in col_names:
            await self._conn.execute("ALTER TABLE products ADD COLUMN is_hidden INTEGER NOT NULL DEFAULT 0")

        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("DB is not connected")
        return self._conn
