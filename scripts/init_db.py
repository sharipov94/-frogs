import asyncio
import aiosqlite
from pathlib import Path

DB_PATH = "shop.db"
SCHEMA_PATH = Path("app/db/schema.sql")


async def main():
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.executescript(schema)
        await db.commit()
    print("DB initialized:", DB_PATH)


if __name__ == "__main__":
    asyncio.run(main())
